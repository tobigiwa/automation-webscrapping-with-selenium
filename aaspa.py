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

import requests, regex
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
def date_transforamtion(start:str = None, end:str = None) -> Tuple[str,str]:
    "Tranfroms date to required formats."
    
    start1 = start.split(',')[1].strip() + ' ' + start.split(',')[2].strip()
    start_date = datetime.strptime(start1, '%B %d %Y').strftime('%Y-%m-%d')

    end1 = end.split(',')[1]
    end2 = re.search('\d\d\d\d', f"{end.split(',')[2]}")
    end_date = end1.strip() + ' ' + str(end2.group())
    end_date = datetime.strptime(end_date, '%B %d %Y').strftime('%Y-%m-%d')

    return start_date, end_date

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
            self.browser.get(url)
            time.sleep(5)
            try:
                all_events = list(filter(lambda x:x.strip() not in ['https://www.aaspa.org/hcle-certification', 'https://www.aaspa.org/events/support-staff-virtual-series-', 'https://www.aaspa.org/webinars'],
                [*set([each.get_attribute('href') for each in self.browser.find_elements(By.CSS_SELECTOR, '.events a')] 
                    + [each.get_attribute('href') for each in self.browser.find_elements(By.CSS_SELECTOR, '.extra-events a')])]))
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.exception('Failed------')
            else: return all_events

        def filter_events(self):
            try:
                sc_event_end_date =  self.browser.find_element(By.CSS_SELECTOR, '.end').text
                sc_event_start_date = self.browser.find_element(By.CSS_SELECTOR, '.start strong').text
                if sc_event_end_date:
                    end =  date_transforamtion(sc_event_start_date, sc_event_end_date)[1]
                    end_date = datetime.strptime(end, '%Y-%m-%d')
                    if end_date < datetime.now():
                            return 'SKIP'
            except: pass

            try:
                date_data = self.browser.find_element(By.CSS_SELECTOR, '.subtitle').text
                match = re.search('(\w+)\s*(\d{1,2})\s*-\s*(\d{1,2})[,]\s*(\d{4})', date_data)
                if match:
                    start, end = f'{match.group(1)} {match.group(2)} {match.group(4)}', f'{match.group(1)} {match.group(3)} {match.group(4)}'
                    end_date = datetime.strptime(end, '%B %d %Y')
                    if end_date < datetime.now():
                        return 'SKIP'
            except: pass


        def get_event(self, url:str) -> NoReturn:
            try:
                self.browser.get(url)
                time.sleep(5)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)


        def event_name(self) -> str:
            "Scrapes and return event name."
            try:
                sc_event_name = self.browser.find_element(By.CSS_SELECTOR, '#ac-event-title').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_name.__name__} Function failed', exc_info=True)
                try:
                    sc_event_name = self.browser.find_element(By.CSS_SELECTOR, '.header-ribbon h1').text
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.event_name.__name__} Function failed', exc_info=True)
                else: return sc_event_name
            else:
                return sc_event_name


        def event_date(self) -> Tuple[str, str]:
            "Scrapes and return event date."
            try:
                sc_event_start_date = self.browser.find_element(By.CSS_SELECTOR, '.start strong').text
                sc_event_end_date =  self.browser.find_element(By.CSS_SELECTOR, '.end').text
            except NoSuchElementException or Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_date.__name__} Function failed', exc_info=True)
                return self.other_date()
            else:
                if sc_event_end_date is None or sc_event_end_date is None:
                    return self.other_date()
                rf_date = date_transforamtion(sc_event_start_date, sc_event_end_date)
                if rf_date:
                    return rf_date
                else: return '', ''

        def other_date(self):
            try:
                date_data = self.browser.find_element(By.CSS_SELECTOR, '.subtitle').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.other_date.__name__} Function failed', exc_info=True)
            else:
                if date_data:
                    match = re.search('(\w+)\s*(\d{1,2})\s*-\s*(\d{1,2})[,]\s*(\d{4})', date_data)
                    if match:
                        start, end = f'{match.group(1)} {match.group(2)} {match.group(4)}', f'{match.group(1)} {match.group(3)} {match.group(4)}'
                        return datetime.strptime(start, '%B %d %Y').strftime('%Y-%m-%d'), datetime.strptime(end, '%B %d %Y').strftime('%Y-%m-%d')
                else: return '', ''


        def event_info(self) -> str:
            "Scrapes and return event info."
            try:
                sc_event_info = self.browser.find_element(By.CSS_SELECTOR, '.details p').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_info.__name__} Function failed', exc_info=True)
                try:
                    sc_event_info = self.browser.find_element(By.CSS_SELECTOR, '.inner-content p').text
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.event_info.__name__} Function failed', exc_info=True)
                else:
                    return sc_event_info
            else:
                return ' '.join(sc_event_info.split('.')[:2])


        def event_timing(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                sc_event_timing = self.browser.find_element(By.CSS_SELECTOR, '.end').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_timing.__name__} Function failed', exc_info=True)
            else:
                match = re.search('([\d\d]+:\d\d \w\w)\s+(\(\w\w\w\))', sc_event_timing)
                if match:
                    return json.dumps([dict(type='general',
                                    Start_time=match.group(1).replace(' ', ''),
                                    end_time='',
                                    timezone=match.group(2).replace('(', '', 1).replace(')', '', 1),
                                    days='all')])
                else:
                    return ''


        def event_ticket_list(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                soup = bs(self.browser.page_source,'html.parser')
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
            else:
                all_text = ' '.join(soup.body.text.split())
                match = re.search('(AASPA members).+(\$\d+).+(\$\d+).+(non-AASPA members).*', all_text)
                match2 = re.search('.+(\$\d+).+( AASPA members).+(\$\d+).+(non AASPA members).*', all_text)
                match3 = re.search('(\$\d+)', all_text)
                if match:
                    temp_use = dict(type=match.group(1), price=match.group(2).replace('$', '', 1).strip(), currency=match.group(2)[0])
                    temp_use2 = dict(type=match.group(4), price=match.group(3).replace('$', '', 1).strip(), currency=match.group(3)[0])
                    return json.dumps([temp_use, temp_use2])
                elif match2:
                    temp_use = dict(type=match2.group(2), price=match2.group(1).replace('$', '', 1).strip(), currency=match2.group(1)[0])
                    temp_use2 = dict(type=match2.group(4), price=match2.group(3).replace('$', '', 1).strip(), currency=match2.group(3)[0])
                    return json.dumps([temp_use, temp_use2])
                elif match3:
                    temp_use = dict(type='paid', price=match3.group(1).replace('$', '', 1).strip(), currency=match3.group(1)[0])
                    return json.dumps([temp_use])
                else:
                    return ''



        def event_mode(self, sc_event_name:str) -> Tuple[str, str, str]:
            """
            Checks the mode of the events.
            Positional parameter is event name.
            Checks for  a selector ".o-details-block__details-info div" in the page for location.
            If element not found, check first paragraph for word "online", "webinar" and "virtual".
            If that returns None, check for another instance or other isntances based on page.
            I agree, a rather tedious and non-friendly and reliably one.
            """
            if 'online' in sc_event_name.lower() or 'virtual' in sc_event_name.lower() or 'webinar' in sc_event_name.lower():
                return 'ONLINE'

            try:
                mode1 = self.browser.find_element(By.CSS_SELECTOR, '.o-details-block__details-info div').text
            except NoSuchElementException or Exception as e:
                mode1 = ''
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_mode.__name__} Function failed', exc_info=True)
                try:
                    all_text = self.browser.find_element(By.CSS_SELECTOR, '.details.inner-content').text
                except NoSuchElementException or Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.event_mode.__name__} Function failed', exc_info=True)
                else:
                    if 'online' in all_text.lower() or 'virtual' in all_text.lower() or 'webinar' in all_text.lower():
                        return 'ONLINE'
                    else:
                        try:
                            mode2 = self.browser.find_element(By.CSS_SELECTOR, '.details.inner-content h5').text
                        except Exception as e:
                            self.error_msg_from_class += '\n' + str(e)
                            logger.error(f'{self.event_mode.__name__} Function failed', exc_info=True)
                        else:
                            rf_mode2 = mode2.split('|')[1].strip()
                            venue, city = rf_mode2.split(',')[0], rf_mode2.split(',')[1]
                            return venue, city, ''

                    try: 
                        venue_data = self.browser.find_element(By.CSS_SELECTOR, '.subtitle').text
                    except NoSuchElementException or Exception as e:
                        self.error_msg_from_class += '\n' + str(e)
                    else:
                        if '|' in venue_data:
                            venue_rf = venue_data.split('|')[1].split(',')[0]
                            return '', venue_rf, ''

                        if len(venue_data.split(',')) == 3:
                            venue_rf = venue_data.split(',')[1].split(' ')[1]
                            return '', venue_rf, ''
            else:
                if mode1:
                    rf_mode1 = mode1.split(',')
                    location = rf_mode1[0].replace('\n', '').strip(), rf_mode1[1].replace('\n', ' ').strip()
                    venue = location[0]
                    match =  re.search('(.+\d+)(.+)', location[1])
                    city, country = match.group(1), match.group(2)
                    return venue, city, country
            

        def event_speakerlist(self) -> json:
            "Scrapes and return a JSONified format of event speaker_list."
            try:
                sc_1  = self.browser.find_element(By.CSS_SELECTOR, '.member').text
            except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
                    return ''
            else:
                name = sc_1.split('\n')[0]
                title = ' '.join(sc_1.split('\n')[1:])
                return json.dumps([dict(name=name, title=title, link='')])


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
                logger.exception(f'function failed')
            else:
                self.browser.close()
                self.browser.switch_to.window(curr_tab)
                return map_url


        def back_page(self) -> NoReturn:
            "Goes a page back."
            self.browser.back()
            time.sleep(0.5)



    base_url = 'https://www.aaspa.org/events/?&Page='

    with ScrapeEvent() as handler:
        " This context manager handles the ScrapeEvent() Class object and handles it teardown for any resource(s) used."
        handler.browser.implicitly_wait(10)
        try:
            events = handler.get_events(base_url)
        except NoSuchElementException or TimeoutException or Exception as e:
            error += '\n' + str(e)
            logger.error(f'{handler.get_events.__name__} Function failed',exc_info=True)
    # end of first part
        i = 0
    # second part
        for each in events:
            i += 1
            try:
                handler.get_event(each)

                past_event = handler.filter_events()
                if past_event == 'SKIP':
                    continue

                # 1 BLOCK CODE: scraping attribute scrappedUrl
                scrappedUrl = each

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
                        eventinfo = f'{eventname.title()}  {startdate}  {enddate}'
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
                orgProfile = 'Our mission is to provide every member with services, resources and information vital to successful school human resource practices in the interest of students.'

                # 9 BLOCK CODE: scraping attribute orgName
                orgName = 'AASPA: American Association of School Personnel Administrators'

                # 10 BLOCK CODE: scraping attribute orgWeb
                orgWeb = 'https://www.aaspa.org/'

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
                    mode = handler.event_mode(str(eventname))
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_mode.__name__} Function failed', exc_info=True)

                # 16, 17 & 18 BLOCK CODE: scraping attribute city, country, venue
                try:
                    if isinstance(mode, tuple):
                        venue = mode[0]
                        city = mode[1]
                        country = mode[2]

                        if len(venue) < 20:
                            city = venue + ' ' + city
                            venue = '     '

                        if city:
                            if re.findall('[A-Z]{2}', city)[-1].lower() in GlobalVariable.states_abv_dict.keys():
                                country='United States'
                                #city = ''

                        
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


                # 21 BLOCK CODE: scraping attribute ContactMail
                try:
                    soup = bs(handler.browser.page_source,'lxml')
                    rex=r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
                    ma=[regex.search(rex,fxc).group() for fxc in ' '.join(soup.body.get_text(separator=' ').split()).lower().split() if regex.search(rex,fxc) != None]
                    mal=[dc[:-1] if dc.endswith('.') else dc for dc in ma]
                    con = list(dict.fromkeys(mal+ ['jennifer@aaspa.org']))
                    if con==[] or con=='':
                        con=['jennifer@aaspa.org']
                except:
                    con = ['jennifer@aaspa.org']

                ContactMail = json.dumps(con, ensure_ascii=False)

                # 22 BLOCK CODE: scraping attribute Speakerlist
                try:
                    Speakerlist = handler.event_speakerlist()
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.event_speakerlist.__name__} Function failed', exc_info=True)
                    Speakerlist = ''

                # 23 BLOCK CODE: scraping attribute online_event
                try:
                    if venue:
                        online_event = 0
                    else:
                        online_event = 1
                except Exception as e:
                    error += '\n' + str(e)
                    online_event = ''

                # 20 BLOCK CODE: scraping attribute googlePlaceUrl
                try:
                    if venue:
                        sc_search_word = f'{venue}'
                        googlePlaceUrl = handler.google_map_url(sc_search_word)
                    else: googlePlaceUrl = ''
                except Exception as e:
                    error += '\n' + str(e)
                    logger.error(f'{handler.google_map_url.__name__} Function failed', exc_info=True)
                    googlePlaceUrl = ''

                data_row = [
                    scrappedUrl, eventname, startdate, enddate, timing,
                    eventinfo, ticketlist, orgProfile, orgName, orgWeb,
                    logo, sponsor, agendalist, type, category, city,
                    country, venue, event_website, googlePlaceUrl,
                    ContactMail, Speakerlist, online_event]

                GlobalFunctions.appendRow(file_name, data_row)


            except Exception as e:
                print(e)
                error += '\n' + str(e) + handler.error_msg_from_class
                logger.error('failed', exc_info=True)
                continue

except Exception as e:
    error += '\n' + str(e)
    logger.error('failed', exc_info=True)
    print(error)

#to save status
GlobalFunctions.update_scrpping_execution_status(file_name, error)


# BYE!!!.

