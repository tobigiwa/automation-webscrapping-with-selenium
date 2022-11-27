# -*- coding: utf-8 -*-
"""
@author: ChewingGumKing_OJF
"""
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from logging import Logger
from random import randint
from typing import Any, Dict, List, NoReturn, Optional, Tuple, Union

import requests
#loads necessary libraries
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

#*******************************************************************************************************************
sys.path.insert(
    0,
    os.path.dirname(__file__).replace('parsing-new-script', 'global-files/'))

#*******************************************************************************************************************

def creating_log(script_name: str, log_folder_path: Optional[str] = None):
    """ 
    Implements the logging module and returns the logger object. 
    Takes a string positional parameter for log file name and a keyword parameter for log file path. 
    Default log file path folder 'log_folder' and each code run clears the last log.
    """

    if not log_folder_path:
        log_folder_path: str = 'log_folder'

    if os.path.exists(log_folder_path):
        for files in os.listdir(log_folder_path):
            if files == f'{os.path.basename(__file__)}.log':
                os.remove(os.path.join(os.getcwd(), log_folder_path, files))
    else:
        os.makedirs(log_folder_path)

    log_path = os.path.join(os.getcwd(), log_folder_path, f'{script_name}.log')

    logger: Logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)
    log_handler = logging.FileHandler(log_path)
    log_format = logging.Formatter(
        '\n %(asctime)s -- %(name)s -- %(levelname)s -- %(message)s \n')
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    logger.info('Log reporting is instantiated.')

    return logger

logger = creating_log(f'{os.path.basename(__file__)}')
#*******************************************************************************************************************
import warnings

from GlobalFunctions import GlobalFunctions
from GlobalVariable import GlobalVariable

warnings.filterwarnings("ignore")

#*******************************************************************************************************************
def date_transforamtion(date: str) -> Tuple[str,str]:
    "Tranfroms date to required formats."
    ...

#*******************************************************************************************************************

error: str = ''

try:
    file_name = sys.argv[1]  #file name from arguments (1st)
    port = int(sys.argv[2])  #port number from arguments (2nd)

    GlobalFunctions.createFile(
        file_name)  #to created TSV file with header line

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")


    path = GlobalVariable.ChromeDriverPath
    driver = webdriver.Chrome(options=options, executable_path=path, port=port)

    @dataclass
    class ScrapeEvent:
        """ 
        The codebase design uses a single Class( dataclass) with it Methods as function scraping singular data (some more though).
        Returns the "self" to a it caller which is handled by a context manager.
        """

        browser: WebDriver = driver
        wait_5sec: WebDriverWait = WebDriverWait(browser, 5)
        error_msg_from_class: str = ''

        def __enter__(self) -> NoReturn:
            "Handles the contex manager."
            return self

        def __exit__(self, exc_type=None, exc_value=None, exc_tb=None) -> NoReturn:
            "Hanles the teardown of the context manager."
            self.browser.quit()

        def dispatch(self, locator:str, strategy:webdriver = By.CSS_SELECTOR):
            "API calls for Selenium webdriver.find_element"
            return self.browser.find_element(strategy, locator)

        def dispatchList(self, locator:str, strategy: webdriver = By.CSS_SELECTOR):
            "API calls for Selenium webdriver.find_elements"
            return self.browser.find_elements(strategy, locator)


        def get_all_info(self, url: str) -> List[str]:
            "Returns a list of all urls"
            self.browser.get(url)
            time.sleep(5)
            try:
                all_url = [each.get_attribute('href') for each in self.dispatchList('.wpb_wrapper h3 a')]
                all_name = [each.text for each in self.dispatchList('.wpb_wrapper h3 a')]
                all_info = [each.text for each in self.dispatchList('.wpb_wrapper p')]
                all_date_and_location = [each.text for each in self.dispatchList('.uavc-list-icon span')]
                all_events_href = [each.get_attribute('href') for each in self.dispatchList('.vc_hidden-sm .vc_column-inner .wpb_wrapper a')]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.exception(f'{self.get_done.__name__} Function failed')
            else:
                filter_blank_space =  lambda var: len(var) > 0
                rough_date_and_location = list(filter(filter_blank_space, all_date_and_location))
                date_and_location = list(zip(*[iter(rough_date_and_location)]*2))

                filter_weed_href = lambda x: '@' not in x and 'uploads' not in x
                all_hrefs = list(filter(filter_weed_href, all_events_href))

                return list(zip(all_url, all_name, all_info, [each[0] for each in date_and_location], [each[1] for each in date_and_location], all_hrefs))


        def google_map_url(self, search_word: str) -> str:
            """
            Returns the result of a Google Maps location search of the parameter.
            This implementation creates a new tab for it job, closes it when done and switch back handle to previous tab.
            """
            try:
                if search_word == 'ONLINE':
                    return 'ONLINE'

                curr_tab = self.browser.current_window_handle
                self.browser.switch_to.new_window('tab')

                map_url = GlobalFunctions.get_google_map_url(search_word, self.browser)

            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)

            else:
                self.browser.close()
                self.browser.switch_to.window(curr_tab)
                return map_url


    base_url = 'https://www.forumsa.gr/ektheseis/'

    with ScrapeEvent() as handler:
        " This context manager handles the ScrapeEvent() Class object and handles it teardown for any resource(s) used."
        handler.browser.implicitly_wait(10)
        try:
            many_info = handler.get_all_info(base_url)
        except NoSuchElementException or TimeoutException or Exception as e:
            error += '\n' + str(e)
            logger.error(f'{handler.get_events.__name__} Function failed',exc_info=True)

        lang_transl = {'ΝΟΕΜΒΡΙΟΥ':'NOVEMBER', 'ΦΕΒΡΟΥΑΡΙΟΥ':'FEBRUARY','ΜΑΡ.':'MARCH', 'ΜΑΡΤΙΟΥ':'MARCH', 'ΜΑΪΟY':'MAY', 'ΣΕΠ':'SEPTEMBER', 'ΝΟΕΜ.':'NOVEMBER'}
        translate_to_eng = lambda v: lang_transl[v]

        def date_transformation(var):
            if '-' in var:
                match = re.search('(\d{1,2})\s*-\s*(\d{1,2})\s*(\S+)\s*(\d{4})', var)
                if match:
                    start, end = f'{translate_to_eng(match.group(3))} {match.group(1)} {match.group(4)}',  f'{translate_to_eng(match.group(3))} {match.group(2)} {match.group(4)}'
                    start_date, end_date = datetime.strptime(start, '%B %d %Y').strftime('%Y-%m-%d'), datetime.strptime(end, '%B %d %Y').strftime('%Y-%m-%d')
                    return start_date, end_date
                else:
                    '', ''
        date_data = list(map(date_transformation, [i[3] for i in many_info]))

    # end of first part

    # second part
        for each in zip(many_info, date_data):
            #print('\npage at event--', i)
            others, date = each[0], each[1]
            try:

                # 1 BLOCK CODE: scraping attribute scrappedUrl
                scrappedUrl = others[0]

                # 2 BLOCK CODE: scraping attribute eventname
                eventname = others[1]
                        
                # 3 & 4 BLOCK CODE: scraping attribute startdate and enddate
                startdate = date[0]
                enddate = date[1]
            
            
                # 5 BLOCK CODE: scraping attribute timing
                timing = ''


                # 6 BLOCK CODE: scraping attribute event_info
                eventinfo = others[2]
                if not eventinfo:
                    eventinfo = f'{eventname.title()}  {startdate} - {enddate}'


                # 7 BLOCK CODE: scraping attribute ticketlist
                ticketlist = ''

                # 8 BLOCK CODE: scraping attribute orgProfile
                orgProfile = 'Εδώ και 34 χρόνια, η FORUM AE, με σεβασμό και αίσθημα ευθύνης απέναντι στους συνεργάτες και στους πελάτες της, δραστηριοποιείται στο χώρο διοργάνωσης εκθέσεων και της έκδοσης επαγγελματικών περιοδικών'

                # 9 BLOCK CODE: scraping attribute orgName
                orgName = 'Forum S.A'

                # 10 BLOCK CODE: scraping attribute orgWeb
                orgWeb = 'https://www.forumsa.gr/'

                # 11 BLOCK CODE: scraping attribute logo
                logo = ''

                # 12 BLOCK CODE: scraping attribute sponsor
                sponsor = ''

                # 13 BLOCK CODE: scraping attribute agendalist
                agendalist = ''

                #14 BLOCK CODE: scraping attribute type
                type = ''
                #15 BLOCK CODE: scraping attribute category
                category = ''


                # 16, 17 & 18 BLOCK CODE: scraping attribute city, country, venue
                venue = others[4]
                city = ''
                country = ''


                # 19 BLOCK CODE: scraping attribute event_website
                event_website = others[5]

                # 20 BLOCK CODE: scraping attribute googlePlaceUrl
                try:
                    if not venue:
                        googlePlaceUrl = ''
                    else:
                        sc_search_word = f'{venue}'
                        gg_map = handler.google_map_url(sc_search_word)
                        googlePlaceUrl = gg_map
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.google_map_url.__name__} Function failed', exc_info=True)
                    googlePlaceUrl = ''

                # 21 BLOCK CODE: scraping attribute ContactMail
                ContactMail = json.dumps(['info@forumsa.gr'])

                # 22 BLOCK CODE: scraping attribute Speakerlist
                Speakerlist = ''

                # 23 BLOCK CODE: scraping attribute online_event
                try:
                    if venue or city:
                        online_event = 0
                    else:
                        online_event = 1
                except Exception as e:
                    error += '\n' + str(e)
                    online_event = ''

                data_row = [
                    scrappedUrl, eventname, startdate, enddate, timing,
                    eventinfo, ticketlist, orgProfile, orgName, orgWeb,
                    logo, sponsor, agendalist, type, category, city,
                    country, venue, event_website, googlePlaceUrl,
                    ContactMail, Speakerlist, online_event]

                GlobalFunctions.appendRow(file_name, data_row)
                #print('done at event--', i, '\n')
                
            except Exception as e:
                print(e)
                error += '\n' + str(e) + handler.error_msg_from_class
                logger.error('failed', exc_info=True)
                print('get here sometimes too')
                continue

except Exception as e:
    error += '\n' + str(e)
    logger.error('failed', exc_info=True)
    print(error)

#to save status
GlobalFunctions.update_scrpping_execution_status(file_name, error)


# BYE!!!.

