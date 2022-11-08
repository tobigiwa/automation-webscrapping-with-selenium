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

event_page = 'https://www.rivieramm.com/events'


def date_transformation(x:str) -> Tuple[str, str]:
        """ handling date transfromation to required format"""
        date_format = '%d %B %Y'
        if '-' in x:
            x = x.strip().lower()
            y = x.split('-')
            start_date = datetime.strptime(y[0].strip(), date_format)
            end_date = datetime.strptime(y[1].strip(),  date_format)
            return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
        else:
            x = x.strip().lower()
            start_date = datetime.strptime(x.strip(), date_format)
            end_date = datetime.strptime(x.strip(),  date_format)
            return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def time_and_location_transformation(x:str, y:str) -> Dict[str, str]:
    """ handling time transfromation to required format"""

    # accounting for time
    x = x.strip()
    x = x.split('-')
    start_time, end_time = x[0].strip(), x[1].strip()
    start_time = datetime.strptime(start_time, '%H:%M').strftime('%I:%M%p')
    end_time = datetime.strptime(end_time, '%H:%M').strftime('%I:%M%p')


    # accounting for location and time zone
    y = y.strip() # removes traling spaces

    if '-' in y:  # accounting for examples like 'BST - ONLINE'
        y = y.split('-')
        time_zone, country = y[0].strip().upper(), y[1].strip().upper()

        return dict(start_time=start_time, end_time=end_time, venue='', city='', country=country, time_zone=time_zone)

    elif len(y.split()) == 1: # accounting single value e,g 'LONDON'
        y = y.upper()
        country = y  
        return dict(start_time=start_time, end_time=end_time, venue='', city='', country=country, time_zone='')

    else:                   # acoounting for values like 'ABCD, DEFG' and 'AB, CD, ED' as venue, city and country
        y = y.split(',')
        if len(y) == 2:
            country, city =y[0].strip().upper(), y[1].strip().upper()
            return dict(start_time=start_time, end_time=end_time, venue='', city=city, country=country, time_zone='')

        elif len(y) == 3:
            venue, city, country = y[0].strip().upper(), y[1].strip().upper(), y[2].strip().upper()
            return dict(start_time=start_time, end_time=end_time, venue=venue, city=city, country=country, time_zone='')
        else:
            pass

#*******************************************************************************************************************

try:
    file_name=sys.argv[1]   #file name from arguments (1st)
    port=int(sys.argv[2])   #port number from arguments (2nd)

    GlobalFunctions.createFile(file_name)   #to created TSV file with header line

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--start-maximized")
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--ignore-certificate-errors')
    # options.add_argument("start-maximized")
    options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    path = GlobalVariable.ChromeDriverPath
    driver = webdriver.Chrome(options=options, executable_path=path, port=port)

    error = ''


    @dataclass
    class ScrapeEvent:
        """ 
        Implements the logging module and returns the logger object. 
        Takes a string positional parameter fro log file name and a keyword parameter for log file path. 
        Default log file path folder 'log_folder' and each code run clears the last log.
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

        def listing_page_urls(self, url:str) -> List[str]:
            "Scrapes and return a list of all eventd urls"
            try:
                self.browser.implicitly_wait(10)
                self.browser.get(url)
                x = self.browser.find_elements(By.CSS_SELECTOR, '.aos-OFVi>div>div>a')
    
                all_links = [i.get_attribute('href') for i in x]
    
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.listing_page_urls.__name__} Function failed', exc_info=True)
            return all_links


        def scrapped_url(self, web_addr:str) -> bool:
            "Gets page"
            try:
                self.browser.get(web_addr)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.scrapped_url.__name__} Function failed', exc_info=True)
            else:
                return True


        def event_title(self) -> str:
            "Scrapes and return event name."
            try:
                title = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located((By.ID, 'aos-EventTitle'))
                ).text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.event_title.__name__} Function failed', exc_info=True)
            else:
                return title


        def date(self) -> Tuple[str, str]:
            "extract and returns both startdate and enddate"
            try:
                sc_date = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located((By.ID, 'aos-ArticleDate'))
                ).text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.date.__name__} Function failed', exc_info=True)
            else:           
                transf_date = date_transformation(sc_date)
                return transf_date 


        def time_and_location(self) -> Dict[str, str]:
            "Scrapes and returns time and location"
            try:
                sc_time = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located((By.ID, 'aos-ArticleTime'))
                ).text
                sc_location = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located((By.ID, 'aos-ArticleLocation'))
                ).text
            except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.time_and_location.__name__} Function failed', exc_info=True)
            else:
                transf_time = time_and_location_transformation(sc_time, sc_location)
                return transf_time
        
        
        def event_venue(self) -> str:
            "Scrapes event venue."
            try:
                self.browser.find_element(By.CSS_SELECTOR, '.aos-TAC[data-tabname=venue]').click()
                # self.browser.find_element(By.LINK_TEXT, 'venue').click()
            except Exception as e:
                error = '\n\n' + str(e)
                return ''
            else:
                try:
                    venues = self.browser.find_element(By.CSS_SELECTOR, '.aos-DS34-WYSEdit.aos-W100 h3').text
                except Exception:
                    try:
                        venues = self.browser.find_element(By.CSS_SELECTOR, '.aos-DS34-WYSEdit.aos-W100 h2').text
                    except Exception as e:
                        self.error_msg_from_class += '\n' + str(e)
                        logger.error(f'{self.get_event.__name__} Function failed', exc_info=True)
                    else:
                        if '\n' in venues:
                            venues = venues.replace('\n', '')
                        self.browser.find_element(By.CSS_SELECTOR, '.aos-TAC[data-tabname=overview]').click()
                        return venues
                    
                else:
                    if '\n' in venues:
                        venues = venues.replace('\n', '')
                    self.browser.find_element(By.CSS_SELECTOR, '.aos-TAC[data-tabname=overview]').click()
                    return venues

        def event_info(self) -> str:
            "Scrapes event info."
            try:
                eventinfo = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.aos-FL100 h2'))
                ).text
                if '\n' in eventinfo:
                    eventinfo = str(eventinfo).replace('\n', ' ')
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                logger.error(f'{self.get_event.__name__} Function failed', exc_info=True)
            else:
                return eventinfo


        def tickect_list(self, *args, **kwargs) -> Dict:
            if not args or kwargs:
                return ' '
            else:
                if args or kwargs == 'free':
                    return ' '


        def org_profile(self, x:str) -> str:
            if not x:
                return ''
            else:
                return x


        def org_name(self, x:str) -> str:
            if not x:
                return ''
            else:
                return x
            


        def org_web(self, x:str) -> str:
            if not x:
                return ''
            else:
                return x


        def google_map_url(self, search_word:str) -> str:
            
            try:
                curr_tab = self.browser.current_window_handle      
                self.browser.switch_to.new_window('tab') 
                self.browser.get('http://google.com')

                try:
                    click_cookie = WebDriverWait(self.browser, ).until(
                        EC.presence_of_element_located((By.ID, 'L2AGLb'))
                        )
                    click_cookie.click()
                except Exception as e:
                    error = '\n\n' + str(e)


                search = WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.NAME, 'q'))
                    )
                search.send_keys(search_word)
                search.send_keys(Keys.RETURN)

                map_url = WebDriverWait(self.browser,10).until(
                        EC.element_to_be_clickable((By.LINK_TEXT, 'Maps'))
                    )
                map_url.click()
                time.sleep(1)
                map_url = self.browser.current_url
                time.sleep(1)
            except Exception as e:
                error = '\n\n' + str(e)
            else:
                self.browser.close()                                       
                self.browser.switch_to.window(curr_tab)
                return map_url


        def contact_mail(self, x) -> dict:
            try:
                self.browser.get(x)
                contact_name = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located((By.ID, 'aos-ContactName'))
                ).text
                contact_email = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located((By.ID, 'aos-ContactEmail'))
                ).text
                a = [contact_email]
            except Exception as e:
                error = '\n\n' + str(e)
            else:
                return a


        def separate_link(self) -> tuple:
            try:
                eventname = WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.aos-OFVi:nth-child(2) .aos-ArticleTitle'))
                    ).text
                if '\n' in eventname:
                    eventname = eventname.replace('\n', '')

                
                date = WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.aos-OFVi:nth-child(2) .aos-ArticleDate'))
                    ).text
                date_format = '%d %b %Y'
                start_date = datetime.strptime(date, date_format).strftime('%Y-%m-%d')
                


                event_time =  WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.aos-OFVi:nth-child(2) .aos-ArticleTime'))
                    ).text
                event_time = datetime.strptime(event_time, '%H:%M').strftime('%I:%M%p')
                time = [json.dumps(
                    dict(type='general',
                    Start_time=event_time,   end_time=event_time,
                    timezone='', days='all'
                    ))]

                raw_location = WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.aos-OFVi:nth-child(2) .aos-ArticleLocation'))
                    ).text 

                y = raw_location.split(',')
                venue, city, country = y[0].strip().upper(), y[1].strip().upper(), y[2].strip().upper()
                location =  dict( venue=venue, city=city, country=country, time_zone='')

                event_info = WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.aos-OFVi:nth-child(2) .aos-ArticleTeaser'))
                    ).text  
                if '\n' in event_info:
                    event_info = event_info.replace('\n', '')

            except Exception as e:
                error = '\n\n' + str(e)
                

            else:
                return eventname, start_date, time, location, event_info




    with ScrapeEvent() as driver:
        """ This context manager handles the ScrapeEvent() Class object and instantiates it caller varaibles"""

    # your code for getting the links of events page from list page and storing them in a list
        links = driver.listing_page_urls(event_page)
        """ LIST OF ALL EVENT LISTINGs"""
        #end of first part

        #second part
        for link in links:
            data_row = []
            try:
                if link == 'https://www.rivieramm.com/international-tug-and-salvage-convention':
                    driver.browser.get(event_page)  
                    # this webpage leads to a different home page and scrapes event from listing page, events of such cab be replicated with this method
                    other_info = driver.separate_link()

                    scrappedUrl = link
                    eventname = other_info[0]
                    startdate = other_info[1]
                    enddate = other_info[1]
                    timing = other_info[2]
                    eventinfo = other_info[4]
                    ticketlist = ''
                    orgProfile = 'Riviera has been providing the maritime, offshore and energy communities with quality multi-platform media services for over 20 years.'
                    orgName = 'Riviera'
                    orgWeb = 'https://www.rivieramm.com/home'
                    logo = ''
                    sponsor = ''
                    agendalist = ''
                    type = ''
                    category = ''
                    city = other_info[3]['city']
                    country = other_info[3]['country']
                    venue = other_info[3]['venue']
                    event_website = link
                    googlePlaceUrl = driver.google_map_url(f'{venue} {city} {country}')
                    ContactMail = [json.dumps('info@rivieramm.com')]
                    Speakerlist = ''
                    if venue is None:
                        online_event = 1
                    else:
                        online_event = 0

                    data_row = [scrappedUrl, eventname, startdate, enddate, timing, eventinfo, ticketlist,
                                orgProfile, orgName, orgWeb, logo, sponsor, agendalist, type, category, city,
                                country, venue, event_website, googlePlaceUrl, ContactMail, Speakerlist, online_event]
                                
                    GlobalFunctions.appendRow(file_name, data_row)
                    continue
                    # break

                # 1  BLOCK CODE:scraping attribute scrappedUrl 
                try:
                    if driver.scrapped_url(link):
                        scrappedUrl = link
                except Exception as e:
                    error = '\n\n' + str(e)
                    scrappedUrl = ' '


                # 2 BLOCK CODE: scraping attribute eventtitle
                try:
                    sc_title = driver.event_title()
                    eventname = sc_title
                except Exception as e:
                    error = '\n\n' + str(e)
                    eventname = ' '

                # 3 BLOCK CODE: scraping attribute startdate and enddate
                try:
                    sc_date = driver.date()
                    startdate = sc_date[0]
                    enddate = sc_date[1]
                except Exception as e:
                    error = '\n\n' + str(e)
                    startdate = ' '
                    enddate = ' '


                # 5 BLOCK CODE: scraping attribute timing
                try:
                    sc_time_location = driver.time_and_location()
                    timing = [json.dumps(
                    dict(type='general',
                    Start_time=sc_time_location['start_time'], end_time=sc_time_location['end_time'],
                    timezone=sc_time_location['time_zone'], days='all'
                    ))]
                except Exception as e:
                    error = '\n\n' + str(e)
                    timing = ' '


                # 6 BLOCK CODE: scraping attribute eventtitle
                try:
                    sc_event_info = driver.event_info()
                    eventinfo = sc_event_info
                except Exception as e:
                    error = '\n\n' + str(e)
                    eventinfo = ' '


                # 7 BLOCK CODE: scraping attribute ticketlist
                try:
                    sc_ticket_list = driver.tickect_list('free')
                    ticketlist = sc_ticket_list
                except Exception as e:
                    error = '\n\n' + str(e)
                    ticketlist = ' '

                profile = 'Riviera has been providing the maritime, offshore and energy communities with quality multi-platform media services for over 20 years.'

                # 8 BLOCK CODE: scraping attribute orgProfile
                try:
                    sc_org_profile = driver.org_profile(profile)
                    orgProfile = sc_org_profile
                except Exception as e:
                    error = '\n\n' + str(e)
                    orgProfile = ' '


                # 9 BLOCK CODE: scraping attribute orgName
                try:
                    sc_name = driver.org_name('Riviera') # Pass a string value of org_name, data can't be scraped from website nor listing page
                    orgName = sc_name
                except Exception as e:
                    error = '\n\n' + str(e)
                    orgName = ' '


                
                # 10 BLOCK CODE: scraping attribute orgWeb
                try:
                    sc_web_name = driver.org_web('https://www.rivieramm.com/home')
                    orgWeb = sc_web_name
                except Exception as e:
                    error = '\n\n' + str(e)
                    orgWeb = ' '


                # 11 BLOCK CODE: scraping attribute logo
                logo = ''


                # 12 BLOCK CODE: scraping attribute sponsor
                try:
                    sponsor = ''
                except Exception as e:
                    error = '\n\n' + str(e)
                    sponsor = ' '


                
                # 13 BLOCK CODE: scraping attribute agendalist
                try:
                    agendalist = ''
                except Exception as e:
                    error = '\n\n' + str(e)
                    agendalist = ' '


                #14 BLOCK CODE: scraping attribute type
                type = ''
                #15 BLOCK CODE: scraping attribute category
                category = ''


                try:
                    if sc_time_location['country'] == 'ONLINE':
                        city = ' '
                        country = ' '
                        venue = ' '
                    else:
                        # 16 BLOCK CODE: scraping attribute city

                        city = sc_time_location['country']  #  yes, did a switch there

                        # 17 BLOCK CODE: scraping attribute country
                        country = sc_time_location['city']

                        # 18 BLOCK CODE: scraping attribute venue
                        # venue = sc_time_location['venue']

                        venue = driver.event_venue()


                except Exception as e:
                    error = '\n\n' + str(e)
                    city = ' '
                    country = ' '
                    venue = ' '


                # 19 BLOCK CODE: scraping attribute event_website
                try:
                    event_website = link
                except Exception as e:
                    error = '\n\n' + str(e)
                    event_website = ' '


                # 20 BLOCK CODE: scraping attribute googlePlaceUrl
                try:
                    if sc_time_location['country'] == 'ONLINE':
                        googlePlaceUrl = ' '
                    elif venue is None or venue == '':
                        googlePlaceUrl = ' '
                    else:
                        search = f"{venue} {sc_time_location['city']} {sc_time_location['country']}"
                        a = driver.google_map_url(search)
                        googlePlaceUrl = a
                except Exception as e:
                    error = '\n\n' + str(e)
                    googlePlaceUrl = ' '


                # 21 BLOCK CODE: scraping attribute ContactMail
                try:
                    sc_contact_mail = driver.contact_mail(link)
                    ContactMail = json.dumps(sc_contact_mail)
                except Exception as e:
                    error = '\n\n' + str(e)
                    contactMail = ' '


                # 22 BLOCK CODE: scraping attribute Speakerlist
                try:
                    Speakerlist = ' '
                except Exception as e:
                    error = '\n\n' + str(e)
                    Speakerlist = ' '


                # 23 BLOCK CODE: scraping attribute online_event
                try:
                    if sc_time_location['country'] == 'ONLINE':
                        online_event = 1
                    else:
                        online_event =  0 
                except Exception as e:
                    error = '\n\n' + str(e)  
                    online_event = ' '

                data_row = [scrappedUrl, eventname, startdate, enddate, timing, eventinfo, ticketlist,
                                orgProfile, orgName, orgWeb, logo, sponsor, agendalist, type, category, city,
                                country, venue, event_website, googlePlaceUrl, ContactMail, Speakerlist, online_event]

                GlobalFunctions.appendRow(file_name, data_row)
            
            except Exception as e:
                    print(e)
                    error += '\n' + str(e) + handler.error_msg_from_class
                    continue

except Exception as e:
    error = '\n\n' + str(e)
    print(error)

#to save status
GlobalFunctions.update_scrpping_execution_status(file_name, error)
