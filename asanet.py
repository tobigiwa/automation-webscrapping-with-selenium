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
def date_transformation(date: str) -> Tuple[str, str]:
    if '-' in date:
        match = re.search('([A-Za-z]+)\s*(\d{1,2})-(\d{1,2}),\s*(\d{4})', date)
        if match:
            start, end = f'{match.group(1)} {match.group(2)} {match.group(4)}', f'{match.group(1)} {match.group(3)} {match.group(4)}'
            start_date, end_date = datetime.strptime(start, '%B %d %Y').strftime('%Y-%m-%d'), datetime.strptime(end, '%B %d %Y').strftime('%Y-%m-%d')
            return start_date, end_date
        else:
            return '', ''
    else:
        date = datetime.strptime(date, '%B %d, %Y').strftime('%Y-%m-%d')
        return date, date
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
    #options.add_argument("--window-size=1920,1080")


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

        def dispatch(self, locator:str, strategy:webdriver = By.CSS_SELECTOR) -> str:
            "API call for selenium.webdriver.remote.webelement.find_element(strategy, locator)"
            return self.browser.find_element(strategy, locator)

        def dispatchList(self, locator:str, strategy:webdriver = By.CSS_SELECTOR)  -> List:
            "API call for selenium.webdriver.remote.webelement.find_elements(strategy, locator)"
            return self.browser.find_elements(strategy, locator)


        def get_all_events(self, url: str) -> List[Tuple[str]]:
            "Returns a list of all urls"
            self.browser.get(url)
            try:
                all_url = [each.get_attribute('href') for each in self.dispatchList('.field-item.even h5 + h3 a')]
                all_event_name = [each.text for each in self.dispatchList('.field-item.even h5 + h3 a')]
                all_event_date = map(date_transformation,[each.text for each in self.dispatchList('.field-item.even h5')])
                all_event_info = [each.text for each in self.dispatchList('.field-item.even h3 +  p')]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
            else:
                return tuple((zip(all_url, all_event_name, all_event_date, all_event_info)))


        def get_each_event(self, url: str) -> NoReturn:
            "Get a singualr event from a list of all events"
            try:
                self.browser.get(url)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_event.__name__} Function failed', exc_info=True)


        def event_mode(self, event_name: str) -> Tuple[str, str]:
            "Scrapes and return event venue "
            if 'webinar' in event_name.lower() or 'virtual' in event_name.lower() or 'online' in event_name.lower():  
                    return 'ONLINE'
            try:
                mode_type = self.dispatch('.field-item.even h3').text
            except Exception or NoSuchElementException as e: 
                self.error_msg_from_class += '\n' + str(e) 
                logger.error(f'{self.event_mode.__name__} Function failed', exc_info=True)
                return ' '
            else:
                if mode_type:
                    mode_type1 = mode_type.split('|')[1]
                    venue, city = mode_type1.split(',')[0], mode_type1.split(',')[1].strip()
                    if re.findall('[A-Z]{2}', city)[0].lower() in GlobalVariable.states_abv_dict.keys():
                        country = 'United States'
                        print('$$$$$$')
                        return venue, city, country
                    else:
                        print('&&&&&&&')
                        return venue, city, ''


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
                logger.error(f'{self.google_map_url.__name__} Function failed', exc_info=True)

            else:
                self.browser.close()
                self.browser.switch_to.window(curr_tab)
                return map_url


    base_url = 'https://www.asanet.org/calendar'

    with ScrapeEvent() as handler:
        " This context manager handles the ScrapeEvent() Class object and handles it teardown for any resource(s) used."
        handler.browser.implicitly_wait(10)
        
        try:
            all_events = handler.get_all_events(base_url)
        except Exception as e:
            error += '\n' + str(e)
            logger.exception(f'{handler.get_all_events.__name__} Function failed')
    # end of first part

    # second part
        index:int = 0
        for each in all_events:

            if each[0] in ['https://forms.office.com/pages/responsepage.aspx?id=LYYGGPBbaEeSFTK-28sJHulnWkvQNWVFi8cde_WCyopUOUtMTjdEMTYwV0RYMFRNODczRUJBWU5XTC4u', 'https://gc-cuny-edu.zoom.us/meeting/register/tZcvf-2prjsrH9EfDyuMtBGbF86rhvKdU5v5', 'https://www.isa-sociology.org/']:
                index += 1
                continue

            print('\npage at event--', index)
            try:
                try:
                    handler.get_each_event(each[0])
                    time.sleep(1)
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.get_each_event.__name__} Function failed', exc_info=True)


                # 1 BLOCK CODE: scraping attribute scrappedUrl
                scrappedUrl = 'https://www.asanet.org/calendar'

                # 2 BLOCK CODE: scraping attribute eventname
                eventname = each[1]

                # 3 & 4 BLOCK CODE: scraping attribute startdate and enddate
                try:
                    startdate, enddate = each[2][0], each[2][1]
                except Exception as e:
                    error += '\n' + str(e)
                    startdate, enddate = '', ''
                
            
                # 5 BLOCK CODE: scraping attribute timing
                timing = ''

                # 6 BLOCK CODE: scraping attribute event_info
                eventinfo = each[3]

                # 7 BLOCK CODE: scraping attribute ticketlist
                ticketlist = ''

                # 8 BLOCK CODE: scraping attribute orgProfile
                orgProfile = 'ASA’s mission is to serve sociologists in their work, advance sociology as a science and profession, and promote the contributions and use of sociology to society.'

                # 9 BLOCK CODE: scraping attribute orgName
                orgName = 'American Sociological Association(ASA)'

                # 10 BLOCK CODE: scraping attribute orgWeb
                orgWeb = 'https://www.asanet.org/about/what-asa'

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

                try:
                    mode = handler.event_mode(eventname)
                except Exception as e:
                    error += '\n' + str(e)
                    logger.exception(f'{handler.event_mode.__name__} Function failed')


                # 16, 17 & 18 BLOCK CODE: scraping attribute city, country, venue
                try:
                    if isinstance(mode, tuple):
                        venue = mode[0]
                        city = mode[1]
                        country = mode[2]
                    elif isinstance(mode, str):
                        venue = ''
                        city = ''
                        country = ''
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_mode.__name__} Function failed', exc_info=True)
                    venue = ''
                    city = ''
                    country = ''


                # 19 BLOCK CODE: scraping attribute event_website
                event_website = handler.browser.current_url

                # 20 BLOCK CODE: scraping attribute googlePlaceUrl
                try:
                    if not venue:
                        googlePlaceUrl = ''
                    else:
                        sc_search_word = f'{venue} {city}'
                        gg_map = handler.google_map_url(sc_search_word)
                        googlePlaceUrl = gg_map
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.google_map_url.__name__} Function failed', exc_info=True)
                    googlePlaceUrl = ''

                # 21 BLOCK CODE: scraping attribute ContactMail
                ContactMail = json.dumps(['asa@asanet.org'])

                # 22 BLOCK CODE: scraping attribute Speakerlist
                Speakerlist = ''

                # 23 BLOCK CODE: scraping attribute online_event
                try:
                    if not venue:
                        online_event = 1
                    else:
                        online_event = 0
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
                print('done at event--', index, '\n')
                index += 1

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

