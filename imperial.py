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

        def get_events(self, url: str) -> List[str]:
            "Returns a list of all urls"
            self.browser.get(url)
            try:
                time.sleep(2.5)
                self.browser.find_element(By.CSS_SELECTOR, '#onetrust-accept-btn-handler').click() 
            except StaleElementReferenceException: pass
            except NoSuchElementException: pass
            except: pass

            flag = True
            while flag:
                try:
                    self.browser.find_element(By.CSS_SELECTOR, '.btn__more').click()
                    flag = True 
                    time.sleep(2)
                except NoSuchElementException or StaleElementReferenceException:
                    flag = False

            container:list = []
            all_event = self.browser.find_elements(By.CSS_SELECTOR, '.event.lg-3.md-6.xs-12')
            for i in range(len(all_event)):
                i += 1
                each_event_date = self.browser.find_elements(By.CSS_SELECTOR, f'.event.lg-3.md-6.xs-12:nth-child({i}) .date time')
                each_event_dates = [g.get_dom_attribute('datetime') for g in each_event_date]
                last_date = each_event_dates[1].split('T')[0]
                rf_datetime = datetime.strptime(last_date, '%Y-%m-%d')
                if rf_datetime > datetime.now():

                    url = self.browser.find_element(By.CSS_SELECTOR, f'.event.lg-3.md-6.xs-12:nth-child({i}) a').get_attribute('href')

                    event_name = self.browser.find_element(By.CSS_SELECTOR, f'.event.lg-3.md-6.xs-12:nth-child({i}) .title').text
                    
                    event_venue = self.browser.find_element(By.CSS_SELECTOR, f'.event.lg-3.md-6.xs-12:nth-child({i}) .venue').text

                    event_type = self.browser.find_element(By.CSS_SELECTOR, f'.event.lg-3.md-6.xs-12:nth-child({i}) .feature.topic').text.replace('\n', '').strip()

                    dates = each_event_dates[0].split('T')[0], last_date

                    container.append((url, event_name, event_venue, event_type , dates))
                    
                else: pass

            return container
        

        def get_event(self, url: str) -> NoReturn:
            "Get a singualr event from a list of all events"
            try:
                self.browser.get(url)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.click_event.__name__} Function failed', exc_info=True)


        def event_timing(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                sc_event_timing = self.browser.find_element(By.CSS_SELECTOR, '.event-details__time--local').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_timing.__name__} Function failed', exc_info=True)
            else:
                match = re.search("(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\s?(\w{3}|\w{2})", sc_event_timing.strip())
                if match:
                    return json.dumps([
                            dict(type='general',
                                Start_time=datetime.strptime(match.group(1),'%H:%M').strftime('%I:%M%p'),
                                end_time=datetime.strptime(match.group(2),'%H:%M').strftime('%I:%M%p'),
                                timezone=match.group(3),
                                days='all')])
                else:
                    return ''

        
        def event_info(self) -> str:
            "Scrapes and return event info."
            try:
                sc_event_info = self.browser.find_element(By.CSS_SELECTOR, '.module.content-hero__body p').text
            except NoSuchElementException: pass
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_info.__name__} Function failed', exc_info=True)
            else:
                match = re.search('(^.+?\.)', sc_event_info.replace('\n', '').strip())
                if match:
                    return match.group(1)
                else:
                    try:
                        sc_event_info = self.browser.find_element(By.CSS_SELECTOR, '.module.content-hero__body p:nth-child(3)').text
                    except NoSuchElementException: pass
                    except Exception as e:
                        self.error_msg_from_class += '\n' + str(e)
                        logger.error(f'{self.event_info.__name__} Function failed', exc_info=True)
                    else:
                        if sc_event_info:
                            return sc_event_info
                        else:
                            return ''
            

        def event_ticket_list(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                sc_event_ticket_list = self.browser.find_element(By.CSS_SELECTOR, '.event-details__label + span').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
            else:
                if 'free' in sc_event_ticket_list.lower().strip():
                    return json.dumps([dict(type='free', price='', currency='')])
                else:
                    return json.dumps([dict(type='paid', price=sc_event_ticket_list[1:], currency=sc_event_ticket_list[0])], ensure_ascii=False)


        def event_mode(self, mode_type: str, event_name: str) -> Tuple[str, str]:
            "Scrapes and return event venue "
            if 'online' in mode_type.lower() or 'webinar' in mode_type.lower() or 'webinar' in event_name.lower() or 'webinar' in event_name.lower():  
                return 'ONLINE'

            if ',' in mode_type:
                if len(mode_type.split(',')) < 3:
                    venue, city = mode_type, ''
                    return venue, city
                    

                elif len(mode_type.split(',')) == 3:
                    venue, city = ''.join(mode_type.split(',')[:2]), ''.join(mode_type.split(',')[2])
                    return venue, city            

                elif len(mode_type.split(',')) > 3:
                    venue, city = ''.join(mode_type.split(',')[:2]), '' 
                    return venue, city
                else:
                    return mode_type, ''
                    
            else:
                return mode_type, ''


        def contactmail(self) -> json:
            try:
                sc_event_contactmail = self.browser.find_elements(By.CSS_SELECTOR, ' .event-details__label + a')
                sc_event_contactmail = [i.get_attribute('href') for i in sc_event_contactmail]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
            else:
                container: List[str] = []
                for i in sc_event_contactmail:
                    if '@' not in i:
                        pass
                    else:
                        container.append(i.replace('mailto:', ''))
                
                return json.dumps(container, ensure_ascii=False)


        def event_speakerlist(self) -> json:
            "Scrapes and return a JSONified format of event speaker_list."
            try:
                speaker  = self.browser.find_element(By.CSS_SELECTOR, '.event-details .event-details__list-content h4').text
            except NoSuchElementException or Exception as e:
                speaker = ''
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)

            try:
                link = self.browser.find_element(By.CSS_SELECTOR, '.event-details .event-details__list-content h4 a').get_attribute('href')
            except NoSuchElementException or Exception as e:
                link = ''
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
                
            try:
                title = self.browser.find_element(By.CSS_SELECTOR, '.event-details__block--speakers .event-details__value').text
            except NoSuchElementException or Exception as e:
                title = ''
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)

            if speaker:
                if title is None or str(title) == 'None':
                    title = ''
                if link is None or str(link) == 'None':
                    link = ''
                return json.dumps([dict(name=speaker, title=title, link=link)], ensure_ascii=False)
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


    base_url = 'https://www.imperial.ac.uk/whats-on/'

    with ScrapeEvent() as handler:
        " This context manager handles the ScrapeEvent() Class object and handles it teardown for any resource(s) used."
        handler.browser.implicitly_wait(10)
        try:
            many_info = handler.get_events(base_url)
        except NoSuchElementException or TimeoutException or Exception as e:
            error += '\n' + str(e)
            logger.error(f'{handler.get_events.__name__} Function failed',exc_info=True)
    # end of first part

    # second part
        for i in range(len(many_info)):
            print('\npage at event--', i)

            try:
                try:
                    handler.get_event(many_info[i][0])
                    time.sleep(1)
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.get_event.__name__} Function failed', exc_info=True)


                # 1 BLOCK CODE: scraping attribute scrappedUrl
                scrappedUrl = handler.browser.current_url

                # 2 BLOCK CODE: scraping attribute eventname
                try:
                    eventname = many_info[i][1]
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_name.__name__} Function failed', exc_info=True)
                    eventname = ''
                        
                # 3 & 4 BLOCK CODE: scraping attribute startdate and enddate
                try:
                    startdate = many_info[i][4][0]
                    enddate = many_info[i][4][1]
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
                        eventinfo = f'{eventname.title()}  {startdate} - {enddate}'
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_timing.__name__} Function failed', exc_info=True)
                    eventinfo = ''


                # 7 BLOCK CODE: scraping attribute ticketlist
                try:
                    ticketlist = handler.event_ticket_list()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_ticket_list.__name__} Function failed', exc_info=True)
                    ticketlist = ''

                # 8 BLOCK CODE: scraping attribute orgProfile
                orgProfile = 'Imperial is a global top ten university with a world-class reputation in science, engineering, business and medicine.'

                # 9 BLOCK CODE: scraping attribute orgName
                orgName = 'Imperial'

                # 10 BLOCK CODE: scraping attribute orgWeb
                orgWeb = 'https://www.imperial.ac.uk/'

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
                    mode = handler.event_mode(many_info[i][2], eventname)
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_mode.__name__} Function failed', exc_info=True)

                # 16, 17 & 18 BLOCK CODE: scraping attribute city, country, venue
                try:
                    if isinstance(mode, tuple):
                        venue = mode[0]
                        city = mode[1]
                        country = 'United Kingdom'
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

