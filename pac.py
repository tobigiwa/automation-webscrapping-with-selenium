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
        start, end = f"{''.join(date.split('-')[0]).strip()} 2022", f"{''.join(date.split('-')[1]).strip()} 2022"
        start_date, end_date = datetime.strptime(start, '%b %d %Y').strftime('%Y-%m-%d'), datetime.strptime(end, '%b %d %Y').strftime('%Y-%m-%d')
        return start_date, end_date
    else:
        date = f"{date} 2022"
        date = datetime.strptime(date, '%b %d %Y').strftime('%Y-%m-%d')
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

        def dispatch(self, class_name:str, finder:webdriver = By.CSS_SELECTOR) -> str:
            "API call for Selenium webdriver.find_element()"
            return self.browser.find_element(finder, class_name)

        def dispatchList(self, class_name:str, finder:webdriver = By.CSS_SELECTOR)  -> List:
            "API call for Selenium webdriver.find_elements()"
            return self.browser.find_elements(finder, class_name)


        def get_events(self, url: str) -> List[str]:
            "Returns a list of all urls"
            self.browser.get(url)
            try:
                all_url = [each.get_attribute('href') for each in self.dispatchList('.event-title a')]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
            else:
                return all_url

        def get_dates(self) -> List[Tuple[str, str]]:
            "TScrapes and returns a list of date"
            try:
                all_dates = [each.text for each in self.dispatchList('.event-date')]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
            else:
                return list(map(date_transformation, all_dates))
        

        def get_event(self, url: str) -> NoReturn:
            "Get a singualr event from a list of all events"
            try:
                self.browser.get(url)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_event.__name__} Function failed', exc_info=True)


        def eventname(self):
            try:
                sc_name = self.dispatch('.rotate-no-rotate')
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.exception(f'{self.eventname.__name__} Function failed')
            else:
                return sc_name.text
            
        
        def event_timing(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                sc_event_timing = ''.join([each.text for each in self.dispatchList('#overview .wpb_wrapper a')])
            except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.exception(f'{self.eventname.__name__} Function failed')
            else:
                match = re.search('(\d{1,2}\s*(?::\d{1,2})?\s*(?:[amp\.]+\.)?)\s*.{1}\s*(\d{1,2}\s*(?::\d{1,2})?\s*(?:[amp\.]+\.)?)\s*([A-Z]{2,3})', sc_event_timing)
                if match:
                    start, end, timezone = match.group(1), match.group(2), match.group(3)
                    if ':' not in start:
                        start = start.split(' ')[0] +':00' + start.split(' ')[-1]

                    start = start.replace(' ', '').replace('.', '').strip().upper()

                    if 'am' not in start.lower() and 'pm' not in start.lower():
                        start = datetime.strptime(start, '%H:%M').strftime('%I:%M%p')
                    
                    if ':' not in end:
                        end = end.split(' ')[0] +':00' + end.split(' ')[-1]

                    end = end.replace(' ', '').replace('.', '').strip().upper()

                    if 'am' not in end.lower() and 'pm' not in end.lower():
                        end = datetime.strptime(end, '%H:%M').strftime('%I:%M%p')

                    start, end = datetime.strptime(start, '%H:%M%p').strftime('%I:%M%p'), datetime.strptime(start, '%H:%M%p').strftime('%I:%M%p')

                return json.dumps([(dict(type='general',
                                        Start_time=start,
                                        end_time=end,
                                        timezone=timezone,
                                        days='all'))], ensure_ascii=False)
        
        def event_info(self) -> str:
            "Scrapes and return event info."
            try:
                sc_event_info = self.dispatch('.white-text .wpb_wrapper p').text 
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.exception(f'{self.event_info.__name__} Function failed')
            else:
                return sc_event_info


        def event_ticket_list(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                self.dispatch('.cc-btn.cc-dismiss').click()
            except: pass
            time.sleep(1)
            try:
                self.dispatch('.vc_toggle_title').click()
            except: pass
            time.sleep(1)

            try:
                event_list = [each.text for each in self.dispatchList('#register .wpb_wrapper li')]
            except Exception as e: 
                self.error_msg_from_class += '\n' + str(e) 
                logger.error(f'{self.get_done.__name__} Function failed', exc_info=True)
                event_list = None

            try:
                event_single = self.dispatch('#register .wpb_wrapper p').text
            except Exception as e: 
                self.error_msg_from_class += '\n' + str(e) 
                logger.error(f'{self.get_done.__name__} Function failed', exc_info=True)
                event_single = None

            if event_list or event_single:
                container: list = [] 
                if event_list:
                    for each in event_list:
                        match = re.search('(\w+[-\s]\w+|\w+)\s*:\s*(\w+|[$]\d+)', each)
                        if match:
                            if  match.group(2).lower() == 'free':
                                container.append(dict(type=match.group(1).strip(), price='0', currency=''))
                            else:
                                container.append(dict(type=match.group(1).strip(), price=''.join(match.group(2).strip()[1:]), currency=match.group(2).strip()[0].replace('F', '').replace('f', '')))
                        else: pass
                    return container

                if event_single:
                    v = event_single.split('\n')[1:]
                    for each in v:
                        if ':' in each:
                            match = re.search('(\w+[-\s]\w+|\w+)\s*:\s*(\w+|[$]\d+)', each)
                            if match:
                                if  match.group(2).lower() == 'free':
                                    container.append(dict(type=match.group(1).strip(), price='0', currency=''))
                                else:
                                    container.append(dict(type=match.group(1).strip(), price=''.join(match.group(2).strip()[1:]), currency=match.group(2).strip()[0].replace('F', '').replace('f', '')))
                            else: pass
                    return container
                        
            else:
                return ''


        def event_mode(self, event_name: str) -> Tuple[str, str]:
            "Scrapes and return event venue "
            try:
                mode_type = self.dispatch('#overview .wpb_wrapper h3').text
            except NoSuchElementException: mode_type = ''
            except Exception as e: 
                self.error_msg_from_class += '\n' + str(e) 
                logger.error(f'{self.event_mode.__name__} Function failed', exc_info=True)
            else:
                if 'online' in mode_type.lower() or 'webinar' in mode_type.lower() or 'virtual' in mode_type.lower() or 'webinar' in event_name.lower() or 'virtual' in event_name.lower() or 'online' in event_name.lower():  
                    return 'ONLINE'
                else:
                    return ''
                    

        def contactmail(self) -> json:
            "Scrapes and return a JSONified format of event contact email(s)."
            try:
                sc_event_contactmail = self.dispatch('email',finder=By.LINK_TEXT).get_attribute('href').replace('mailto:', '').replace('https://pac.org/', '')
            except NoSuchElementException: sc_event_contactmail = ''
            except Exception as e: 
                self.error_msg_from_class += '\n' + str(e) 
                logger.error(f'{self.contactmail.__name__} Function failed', exc_info=True)
            else:
                if '@' not in sc_event_contactmail:
                    return ''

                if sc_event_contactmail:
                    return json.dumps([sc_event_contactmail], ensure_ascii=False)

                else:
                    return ''

        def event_speakerlist(self) -> json:
            "Scrapes and return a JSONified format of event speaker_list."
            try:
                all_speaker = [each.text for each in self.dispatchList('#featured .vc_align_center + .wpb_text_column.wpb_content_element p')]
            except NoSuchElementException: all_speaker = None
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_events.__name__} Function failed', exc_info=True)
            else:
                if all_speaker:
                    def split_speaker_and_title(x: str) -> list:
                        name, title = ''.join(x.split('\n')[0]), ''.join(x.split('\n')[1:])
                        return dict(name=name, title=title, link='')

                    return json.dumps(list(map(split_speaker_and_title, all_speaker)), ensure_ascii=False)
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


    base_url = 'https://pac.org/events/upcoming'

    with ScrapeEvent() as handler:
        " This context manager handles the ScrapeEvent() Class object and handles it teardown for any resource(s) used."
        handler.browser.implicitly_wait(10)
        try:
            all_events = handler.get_events(base_url)
        except NoSuchElementException or TimeoutException or Exception as e:
            error += '\n' + str(e)
            logger.exception(f'{handler.get_events.__name__} Function failed')
    # end of first part

    # second part
        try:
            all_dates = handler.get_dates()
        except NoSuchElementException or TimeoutException or Exception as e:
            error += '\n' + str(e)
            logger.error(f'{handler.get_dates.__name__} Function failed',exc_info=True)
        
        index:int = 0
        for i in all_events:

            
            if i in ['https://pac.org/event/eur/eudas2022', 'https://pac.org/events/institute', 'https://pac.org/events/the-advocacy-conference', 'https://pac.org/events/pac-conference/']:
                index += 1
                continue

            print('\npage at event--', index)

            try:
                try:
                    handler.get_event(i)
                    time.sleep(1)
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.get_event.__name__} Function failed', exc_info=True)


                # 1 BLOCK CODE: scraping attribute scrappedUrl
                scrappedUrl = handler.browser.current_url

                # 2 BLOCK CODE: scraping attribute eventname
                try:
                    eventname = handler.eventname()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.eventname.__name__} Function failed', exc_info=True)
                    eventname = ''
                        
                # 3 & 4 BLOCK CODE: scraping attribute startdate and enddate
                try:
                    startdate = all_dates[index][0]
                    enddate = all_dates[index][1]
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_date.__name__} Function failed', exc_info=True)
                    startdate = ''
                    enddate = ''
                
            
                # 5 BLOCK CODE: scraping attribute timing
                try:
                    timing = handler.event_timing()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_timing.__name__} Function failed', exc_info=True)
                    timing = ''


                # 6 BLOCK CODE: scraping attribute event_info
                try:
                    eventinfo = handler.event_info()
                    if not eventinfo:
                        eventinfo = f'Theme: {eventname.title()} + {startdate} - {enddate}'
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_info.__name__} Function failed', exc_info=True)
                    eventinfo = ''


                # 7 BLOCK CODE: scraping attribute ticketlist
                try:
                    ticketlist = handler.event_ticket_list()
                    if ticketlist:
                        ticketlist = json.dumps(ticketlist, ensure_ascii=False)
                    else: ticketlist = ''
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_ticket_list.__name__} Function failed', exc_info=True)
                    ticketlist = ''

                # 8 BLOCK CODE: scraping attribute orgProfile
                orgProfile = 'The Public Affairs Council is THE community for public affairs professionals. Our mission is to advance the field of public affairs and to provide members with the executive education, expertise and research they need to succeed while maintaining the highest ethical standards.'

                # 9 BLOCK CODE: scraping attribute orgName
                orgName = 'Public Affairs Council'

                # 10 BLOCK CODE: scraping attribute orgWeb
                orgWeb = 'https://pac.org/'

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
                    logger.error(f'{handler.event_mode.__name__} Function failed', exc_info=True)

                # 16, 17 & 18 BLOCK CODE: scraping attribute city, country, venue
                try:
                    if isinstance(mode, tuple):
                        venue = mode[0]
                        city = mode[1]
                        country = ''
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
                        sc_search_word = f'{venue} {city}'
                        gg_map = handler.google_map_url(sc_search_word)
                        googlePlaceUrl = gg_map
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.google_map_url.__name__} Function failed', exc_info=True)
                    googlePlaceUrl = ''

                # 21 BLOCK CODE: scraping attribute ContactMail
                try:
                    ContactMail = handler.contactmail()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.contactmail.__name__} Function failed', exc_info=True)
                    ContactMail = ''

                # 22 BLOCK CODE: scraping attribute Speakerlist
                try:
                    Speakerlist = handler.event_speakerlist()
                    if Speakerlist is None:
                        Speakerlist = ''
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

