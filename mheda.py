# -*- coding: utf-8 -*-
"""
@author: ChewingGumKing_OJF
"""
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from random import randint
from typing import Any, Dict, List, NoReturn, Optional, Tuple, Union

import requests
#loads necessary libraries
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
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
import logging


def creating_log(script_name: str, log_folder_path: Optional[str] = None):
    """ 
    Implements the logging module and returns the logger object. 
    Takes a string positional parameter fro log file name and a keyword parameter for log file path. 
    Default log file path folder 'log_folder' and each code run clears the last log.
    """

    if not log_folder_path:
        log_folder_path: str = 'log_folder'

    if os.path.exists(log_folder_path):
        for files in os.scandir(log_folder_path):
            os.remove(files)
    else:
        os.makedirs(log_folder_path)

    log_path = os.path.join(os.getcwd(), log_folder_path, f'{script_name}.log')

    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)
    log_handler = logging.FileHandler(log_path)
    log_format = logging.Formatter(
        '%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s \n\n')
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
    if '-' not in date:
        return  datetime.strptime(date.replace(',', '').strip(), '%B %d %Y').strftime('%Y-%m-%d'), ''
    elif '-' in date:
        match = re.search('(\d\d\d\d)', date)
        if match:
            year = match.group(1)
        start, end = str(date.split('-')[0]) + ' ' + str(year), date.split('-')[1].replace(',', '')
        return datetime.strptime(start.strip(), '%B %d %Y').strftime('%Y-%m-%d'), datetime.strptime(end.strip(), '%B %d %Y').strftime('%Y-%m-%d')
    else:
        return ''

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
    options.add_argument("--window-size=1920,1080")


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

        def get_events(self, url: str) -> List[str]:
            "Returns a list of all urls"
            try:
                self.browser.get(url)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_event.__name__} Function failed', exc_info=True)
            else:
                try:
                    _event = self.browser.find_elements(By.CSS_SELECTOR, '.entry-title a')
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.get_event.__name__} Function failed', exc_info=True)
                else:
                    all_events = [i.get_attribute('href') for i in _event]
                    return all_events


        def get_event(self, url: str) -> NoReturn:
            "Get a singualr event from a list of all events"
            try:
                self.browser.get(url)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.click_event.__name__} Function failed', exc_info=True)


        def event_name(self) -> str:
            "Scrapes and return event name."
            try:
                sc_event_name = self.browser.find_element(By.CSS_SELECTOR, '.entry-title').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_name.__name__} Function failed', exc_info=True)
            else:
                return sc_event_name.replace('\n', '')


        def event_date(self) -> Tuple[str, str]:
            "Scrapes and return event date."
            try:
                sc_event_date = self.browser.find_element(By.CSS_SELECTOR, '.entry-date').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_date.__name__} Function failed', exc_info=True)
                try:
                    sc_event_date1 = self.browser.find_element(By.CSS_SELECTOR, '.page-content-inner p').text
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.event_date.__name__} Function failed', exc_info=True)
                else:
                    rf_date = sc_event_date1.split('\n')[0]
                    rf_date = date_transforamtion(rf_date)
                    if rf_date:
                        return rf_date
                    else:
                        return '', ''
            else:
                rf_date = date_transforamtion(sc_event_date)
                if rf_date:
                    return rf_date
                else:
                    return '', ''

        
        def event_info(self) -> str:
            "Scrapes and return event info."
            try:
                sc_event_info = self.browser.find_element(By.CSS_SELECTOR, '.entry-meta.meta').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_info.__name__} Function failed', exc_info=True)
                try:
                    info2_ = self.browser.find_element(By.CSS_SELECTOR, '.page-content-inner p').text
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.event_info.__name__} Function failed', exc_info=True)
                else:
                    return ' '.join(info2_.split('\n')[1:])
            else:
                return sc_event_info


        def event_timing(self, info: str) -> json:
            "Scrapes and return a JSONified format of event timing."
            match1 = re.search('([\d\d]:\d\d ..)', info)
            match2 = re.search('(–[\d\d]:\d\d ..)', info)
            if match1:
                start_time = match1.group(1).replace(' ', '')
            else:
                start_time = ''
            if match2:
                end_time = match2.group(1).replace('–', '').replace(' ', '')
            else:
                end_time = ''

            if start_time and not end_time:
                return [
                        json.dumps(
                            dict(type='general',
                                Start_time=start_time,
                                end_time='',
                                timezone='ET',
                                days='all'))
                    ]
            elif start_time and end_time:
                return [
                        json.dumps(
                            dict(type='general',
                                Start_time=start_time,
                                end_time=end_time,
                                timezone='ET',
                                days='all'))
                    ]
            else:
                return ''


        def event_ticket_list(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                all_p_tags = self.browser.find_elements(By.TAG_NAME, 'p')
                p_tags = [i.text for i in all_p_tags]
                text = ' '.join(p_tags)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
            else:
                match =  re.findall('(\$\d+) (\w+|Non-Member) (\w+)', text)
                match2 = re.search('free', text)

                container: List[Dict[str, str]] = []
                if match:
                    for i in match:
                        fee = i[0].replace('$', '')
                        type = i[1] + ' ' + i[2]
                        if 'today' in type or 'in' in type:
                            continue
                        temp_use = dict(type=type, price=fee, currency=i[0][0])
                        container.append(temp_use.copy())
                    return json.dumps(container)
                elif match2:
                    return json.dumps([dict(type='free', price='', currency='')])
                else:
                    return ''


        def event_mode(self, event_info:str) -> Tuple[str, str, str]:
            """
            Checks the mode of the events.
            Positional parameter is event info.
            The functions works on the parameter to define event mode.
            """
            if 'online' in event_info.lower() or 'virtual' in event_info.lower() or 'webinar' in event_info.lower():
                return 'ONLINE'

            if '-' in event_info:
                part1 = event_info.split('-')[1]
                if len(part1.split(',')) == 3:
                    venue, city = ' '.join(part1.split(',')[:2]), part1.split(',')[-1]
                    return venue, city, ''
                if len(part1.split(',')) == 2:
                    venue, city = part1.split(',')[0], part1.split(',')[-1]
                    return venue, city, ''
            else:
                if len(event_info.split(',')) == 2:
                    venue, city = event_info.split(',')[0], event_info.split(',')[-1]
                    return venue, city, ''

            return 'ONLINE'
            

        def event_speakerlist(self) -> json:
            "Scrapes and return a JSONified format of event speaker_list."
            try:
                sc_1  = self.browser.find_elements(By.CSS_SELECTOR, '.event-speaker h2')
            except NoSuchElementException or Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
                return ''
            else:
                hold: List = []
                if sc_1:
                    for i in sc_1:
                        temp_use = dict(name=i.text, title='', link='')
                        hold.append(temp_use.copy())
                    return json.dumps(hold, ensure_ascii=False)
                else:
                    return ''


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

                self.browser.get('http://google.com')
                search = self.wait_5sec.until(
                    EC.presence_of_element_located((By.NAME, 'q')))

                search.send_keys(search_word)
                search.send_keys(Keys.RETURN)

                map_url = WebDriverWait(self.browser, 3).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, 'Maps')))
                map_url.click()
                time.sleep(0.5)
                map_url = self.browser.current_url
            
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.google_map_url.__name__} Function failed', exc_info=True)

            else:
                self.browser.close()
                self.browser.switch_to.window(curr_tab)
                return map_url


    base_url = 'https://www.mheda.org/events/'

    with ScrapeEvent() as handler:
        " This context manager handles the ScrapeEvent() Class object and handles it teardown for any resource(s) used."
        handler.browser.implicitly_wait(10)
        try:
            events = handler.get_events(base_url)
        except NoSuchElementException or TimeoutException or Exception as e:
            error += '\n' + str(e)
            logger.error(f'{handler.get_events.__name__} Function failed',exc_info=True)
    # end of first part

    # second part
        i = 0
        for link in events:
            i += 1

            if link == 'https://www.promatshow.com/':
                continue

            print('\npage at event--', i)
            try:
                handler.get_event(link)
                time.sleep(1)

                # 1 BLOCK CODE: scraping attribute scrappedUrl
                scrappedUrl = handler.browser.current_url

                # 2 BLOCK CODE: scraping attribute eventname
                try:
                    eventname = handler.event_name()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_name.__name__} Function failed', exc_info=True)
                    eventname = ''
                        
                # 3 & 4 BLOCK CODE: scraping attribute startdate and enddate
                try:
                    date = handler.event_date()
                    startdate = date[0]
                    enddate = date[1]
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_date.__name__} Function failed', exc_info=True)
                    startdate = ''
                    enddate = ''
                
                # 6 BLOCK CODE: scraping attribute event_info
                try:
                    eventinfo = handler.event_info()
                    if not eventinfo:
                        eventinfo = f'Theme: {eventname.title()} + {startdate} - {enddate}'
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_info.__name__} Function failed', exc_info=True)
                    eventinfo = ''

                # 5 BLOCK CODE: scraping attribute timing
                try:
                    timing = handler.event_timing(eventinfo)
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_timing.__name__} Function failed', exc_info=True)
                    timing = ''


                # 7 BLOCK CODE: scraping attribute ticketlist
                try:
                    ticketlist = handler.event_ticket_list()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_ticket_list.__name__} Function failed', exc_info=True)
                    ticketlist = ''

                # 8 BLOCK CODE: scraping attribute orgProfile
                orgProfile = 'MHEDA is the Material Handling Equipment Distributors Association, a 501(c)6 non-profit trade association, dedicated to serving all segments of the material handling business community.'

                # 9 BLOCK CODE: scraping attribute orgName
                orgName = 'MHEDA'

                # 10 BLOCK CODE: scraping attribute orgWeb
                orgWeb = 'https://www.mheda.org/about-us/'

                # 11 BLOCK CODE: scraping attribute logo
                logo = ''

                # 12 BLOCK CODE: scraping attribute sponsor
                #sponsor = handler.event_sponsor(index)
                sponsor = ''

                # 13 BLOCK CODE: scraping attribute agendalist
                agendalist = ''

                #14 BLOCK CODE: scraping attribute type
                type = ''
                #15 BLOCK CODE: scraping attribute category
                category = ''

                try:
                    mode = handler.event_mode(str(eventinfo))
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_mode.__name__} Function failed', exc_info=True)

                # 16, 17 & 18 BLOCK CODE: scraping attribute city, country, venue
                try:
                    if isinstance(mode, tuple):
                        venue = mode[0]
                        city = mode[1]
                        country = mode[2]
                    elif isinstance(mode, str):
                        if mode == 'ONLINE':
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
                event_website = scrappedUrl

                # 20 BLOCK CODE: scraping attribute googlePlaceUrl
                try:
                    if not venue:
                        googlePlaceUrl = ''
                    else:
                        sc_search_word = f'{venue} {city} {country}'
                        gg_map = handler.google_map_url(sc_search_word)
                        googlePlaceUrl = gg_map
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.google_map_url.__name__} Function failed', exc_info=True)
                    googlePlaceUrl = ''

                # 21 BLOCK CODE: scraping attribute ContactMail
                ContactMail = json.dumps(['connect@mheda.org'])

                # 22 BLOCK CODE: scraping attribute Speakerlist
                try:
                    Speakerlist = handler.event_speakerlist()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_speakerlist.__name__} Function failed', exc_info=True)
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
                print('done at event--', i, '\n')
                
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

