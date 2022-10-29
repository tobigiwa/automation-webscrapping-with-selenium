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
from typing import Any, List, NoReturn, Optional, Tuple, Union

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

    log_path: str = os.path.join(os.getcwd(), log_folder_path, f'{script_name}.log')

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
def date_transforamtion(sc_date: str) -> Union[tuple,str]:
    "Tranfroms date to required formats."

    match = re.search('([a-zA-Z]+)\s*(.+),\s*(\d\d\d\d)', sc_date)
    if match:
        day1, day2 = match.group(2).split('-')[0].strip(), match.group(2).split('-')[1].strip()
        start_date = f'{day1} {match.group(1)} {match.group(3)}'
        end_date = f'{day2} {match.group(1)} {match.group(3)}'
        start_date = datetime.strptime(start_date, '%d %B %Y')
        end_date = datetime.strptime(end_date, '%d %B %Y')
        print(start_date, end_date,)
        if start_date < datetime.now():
            print('PAST EVENT')
            return 'PAST EVENT'
        else:
            print('RELEVANT EVENT')
            print(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

            return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    else:
        return 'MATCH FAILED'


def event_mode(mode: str) -> str:
    "Confirms event mode."

    if 'virtual' in mode.lower():
        return 'ONLINE'
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

        def get_events(self, url: str) -> int:
            "Returns the total number of events on the page."
            try:
                self.browser.get(url)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_event.__name__} Function failed', exc_info=True)
            else:
                try:
                    all_event = self.browser.find_elements(By.CSS_SELECTOR, '.MuiGrid-grid-lg-3.css-1etv89n')
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.get_event.__name__} Function failed', exc_info=True)
                else:
                    return len(all_event)


        def click_event(self, index:int) -> NoReturn:
            "Uses selenium ActionChains to navigate to single event by index and clicks it."
            try:
                time.sleep(1.5)
                all_events = self.browser.find_elements(By.CSS_SELECTOR, '.MuiGrid-grid-lg-3.css-1etv89n')
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.click_event.__name__} Function failed', exc_info=True)
            else:
                page = all_events[index]
                try:
                    ActionChains(self.browser).move_to_element(page).click(on_element=page).perform()
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.click_event.__name__} Function failed', exc_info=True)
                else:
                    time.sleep(0.5)


        def scrapped_one(self) -> Tuple[str, str, str, str, str]:
            """
            Scrapes and return a tuple containing the current page URL, event name, event date, event location, event mode respectively.
            Scraping individual data was not possible as all data was within ths same paragraph.
            """
            try:
                time.sleep(1.5)
                sc_one = self.browser.find_elements(By.CSS_SELECTOR, 'main p')
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.scrapped_one.__name__} Function failed', exc_info=True)
            else:
                needed = sc_one[:4]
                del sc_one
                rf_needed = [i.text for i in needed]
                curr_url = self.browser.current_url
                sc_eventname = rf_needed[0]
                sc_eventdate = date_transforamtion(rf_needed[1])
                sc_eventlocation = rf_needed[2].split(',')[0], rf_needed[2].split(',')[1]
                sc_eventmode = event_mode(rf_needed[3])
                return curr_url, sc_eventname, sc_eventdate, sc_eventlocation, sc_eventmode

        
        def event_info(self) -> str:
            "Scrapes and return event info."
            try:
                sc_event_info = self.browser.find_element(By.CSS_SELECTOR, '#about p:nth-child(2)').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_info.__name__} Function failed', exc_info=True)
            else:
                return sc_event_info


        def event_timing(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                sc_event_timing = self.browser.find_elements(By.CSS_SELECTOR, '#agenda .css-1dwb3pr')
                sc_event_timing= [i.text for i in sc_event_timing]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_timing.__name__} Function failed', exc_info=True)
            else:
                if sc_event_timing:
                    start_time = datetime.strptime(sc_event_timing[0].split('-')[0].strip(), '%H.%M').strftime('%I:%M%p')
                    end_time = datetime.strptime(sc_event_timing[-1].split('-')[1].strip(), '%H.%M').strftime('%I:%M%p')
                    return [
                            json.dumps(
                                dict(type='general',
                                    Start_time=start_time,
                                    end_time=end_time,
                                    timezone='',
                                    days='all'))
                        ]
                else:
                    return ''

        def event_ticket_list(self) -> json:
            "Scrapes and return a JSONified format of event ticket_list."

            try:
                sc_event_ticketlist  = self.browser.find_elements(By.CSS_SELECTOR, '#plans .items-center')
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                hold:List[str ] = []
                sc_ticketlist = [i.text for i in sc_event_ticketlist]
                type = sc_ticketlist[0::3]
                fee = sc_ticketlist[1::3]
                for i in zip(type, fee):
                    temp_use = dict(type=i[0], price=i[1].replace('$', '', 1).strip(), currency=i[1][0])
                    hold.append(temp_use.copy())
                if hold:
                    return json.dumps(hold, ensure_ascii=False)
                else:
                    return ''


        def event_venue(self) -> str:
            "Scrapes and return event venue."
            try:
                sc_event_venue  = self.browser.find_element(By.CSS_SELECTOR, '#venue div div p').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_venue.__name__} Function failed', exc_info=True)
            else:
                if str(sc_event_venue).strip().lower() in ['venue will be updated soon.', 'venue will be updated soon..', 'Venue will be updated soon..', 'Venue will be updated soon.']:
                    return ''
                else:
                    return sc_event_venue


        def event_speakerlist(self) -> json:
            "Scrapes and return a JSONified format of event speaker_list."
            try:
                sc_1  = self.browser.find_elements(By.CSS_SELECTOR, '#agenda h6')
                sc_2  = self.browser.find_elements(By.CSS_SELECTOR, '#agenda h6+ p')
                s_3 = [i.text for i in sc_1]
                s_4 = [i.text for i in sc_2]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
            else:
                l: List[str] = []
                for i in zip(s_3, s_4):
                    if i[0] not in ['REGISTRATIONS','STAR','Speaker','SCIENCE CAFE','LUNCH BREAK']:
                        if i[0] == '-':
                            continue
                        temp_use = dict(name=i[0], title=i[1].replace('-', '', 1), link='')
                        l.append(temp_use.copy())
                if l:
                    return json.dumps(l, ensure_ascii=False)
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
                    logger.exception(f'function failed')
                else:
                    self.browser.close()
                    self.browser.switch_to.window(curr_tab)
                    return map_url


        def back_page(self) -> NoReturn:
            "Goes a page back."
            self.browser.back()
            time.sleep(0.5)



    base_url = 'https://www.starconferences.org/conferences'

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
        for i in range(events):
            print('\npage at event--', i+1)
            try:
                handler.click_event(i)
                time.sleep(1)

                # 1 & 2 BLOCK CODE: scraping attribute scrappedUrl and eventname
                try:
                    many_data = handler.scrapped_one()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.scrapped_one.__name__} Function failed',exc_info=True)
                else:
                    print('many-data[2]----', many_data[2])
                    if many_data[2] == 'PAST EVENT':
                        print('checks at past event')
                        handler.back_page()
                        continue
                    else:
                        try:
                            scrappedUrl = many_data[0]
                            eventname = many_data[1]
                            print(eventname)
                        except Exception as e:
                            error += '\n' + str(e)
                            scrappedUrl = ''
                            eventname = ''

                        
                # 3 & 4 BLOCK CODE: scraping attribute startdate and enddate
                try:
                    if many_data[2] == 'MATCH FAILED':
                        print('MATCH FAILED')
                        print(many_data[1])
                        print(many_data)
                        handler.back_page()
                        continue
                    else:
                        sc_date = many_data[2]
                        startdate = sc_date[0]
                        enddate = sc_date[1]
                except Exception as e:
                    error += '\n' + str(e)
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
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_ticket_list.__name__} Function failed', exc_info=True)
                    ticketlist = ''

                # 8 BLOCK CODE: scraping attribute orgProfile
                orgProfile = 'STAR Conferences is extremely passionate in 3C’s, Creating, Connections and Conversions among research scientists and researchers as leading experts to integrate B2B businesses among individuals, and companies to connect, communicate, cultivate, and convert research ideas elegantly and efficiently for human mankind.'

                # 9 BLOCK CODE: scraping attribute orgName
                orgName = 'STAR Conferences'

                # 10 BLOCK CODE: scraping attribute orgWeb
                orgWeb = 'https://www.starconferences.org/'

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

                # 16 BLOCK CODE: scraping attribute city
                try:
                    city = many_data[3][0]
                except Exception as e:
                    error += '\n' + str(e)
                    city = ''

                # 17 BLOCK CODE: scraping attribute country
                try:
                    country = many_data[3][1]
                except Exception as e:
                    error += '\n' + str(e)
                    country = ''

                # 18 BLOCK CODE: scraping attribute venuev
                try:
                    sc_venue = many_data[4]
                    if sc_venue == 'ONLINE':
                        venue = ''
                    else:
                        venue = handler.event_venue()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_venue.__name__} Function failed', exc_info=True)
                    venue = ''

                # 19 BLOCK CODE: scraping attribute event_website
                event_website = scrappedUrl

                # 20 BLOCK CODE: scraping attribute googlePlaceUrl
                try:
                    if sc_venue == 'ONLINE' or not venue:
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
                ContactMail = json.dumps(['customerservice@starconferences.org'])

                # 22 BLOCK CODE: scraping attribute Speakerlist
                try:
                    Speakerlist = handler.event_speakerlist()
                    print('speakerlist ----', Speakerlist)
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_speakerlist.__name__} Function failed', exc_info=True)
                    Speakerlist = ''

                # 23 BLOCK CODE: scraping attribute online_event
                try:
                    if sc_venue == 'ONLINE':
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
                print('done at event--', i+1, '\n')
                handler.back_page()

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
