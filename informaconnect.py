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
from typing import Any, Dict, List, NoReturn, Optional, Sequence, Tuple, Union

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

import json
#*******************************************************************************************************************
import warnings

import requests
from GlobalFunctions import GlobalFunctions
from GlobalVariable import GlobalVariable

warnings.filterwarnings("ignore")

#*******************************************************************************************************************

home_url = 'https://www.informaconnect.com.sg/'

def date_transformation(s:str) -> Tuple[str, str]:
    """ handling date transfromation to required format"""

    date_format = '%d %b %Y'
    if '-' in s:
        v = s.split(' - ')
        month_year = v[1].split(' ', 1)[1].strip()
        year = month_year[-4:]
        v[0] += f' {year}' if len(v[0].split(' ', 1)) > 1 else f' {month_year}'
        return datetime.strptime(v[0],date_format).strftime('%Y-%m-%d'), datetime.strptime(v[1],date_format).strftime('%Y-%m-%d')
    else:
        return datetime.strptime(s, date_format).strftime('%Y-%m-%d'), datetime.strptime(s, date_format).strftime('%Y-%m-%d')


def location(x: str) -> Tuple[str, str]:
    """ handling location transfromation to required format"""
    if 'Online' in x or 'Blended' in x:
        return 'ONLINE'
    else:
        if ',' in x:
            x = x.split(',') # the comma is the best way to denote a city and country... a whitespace would fail in case of `United States`
            city, country = x[0], x[1]
            return city, country
        else:
            return ' ', x


def ticket_fee(input:str) -> Tuple[str, str]:
    """ handling ticket transfromation to required format"""
    result = re.findall("^(?:[A-Z]{3})?\s*(.{1})\s*(\d+(?:\.\d+)?)$", input)
    b, c = result[0]
    return b, c
#*******************************************************************************************************************

try:
    file_name=sys.argv[1]   #file name from arguments (1st)
    port=int(sys.argv[2])   #port number from arguments (2nd)

    GlobalFunctions.createFile(file_name)   #to created TSV file with header line

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    path = GlobalVariable.ChromeDriverPath
    driver = webdriver.Chrome(options=options, executable_path=path, port=port)

    error = ''  

    @dataclass
    class ScrapeEvent:
        """ the codebase design uses a Class with it Methods as function scraping singular data(some more,
        in the case of going inside the page just once). It returns the data to a it caller which is handled by a context manager
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

        def navigate_to_eventpage(self, x:str) -> NoReturn :
            """gets us from the home page to the event listing page, runs once"""
            self.browser.implicitly_wait(10)
            try:
                self.browser.get(x)
                WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.LINK_TEXT, 'See all events'))
                ).click()
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)

        def listing_page_urls(self) -> List[str]:
            """Extract the length of events i.e 'hrefs' present, this is use in iterating"""
            try:
                events = self.browser.find_elements(By.CSS_SELECTOR, '.event-cnt a')
                event_boxes_urls = [i.get_attribute('href') for i in events]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                return event_boxes_urls
        

        def refresh_page(self) -> NoReturn:
            time.sleep(1)
            self.browser.refresh() 
            time.sleep(1.5)


        def get_event(self, url:str) -> NoReturn:
            try:
                self.browser.get(url)
                time.sleep(3)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                


        def scrapped_url(self) -> str:
            """ scrapes the url"""
            try:
                ScrappedUrl = self.browser.current_url
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                return ScrappedUrl


        def event_name(self) -> str:
            "Scrapes and return event name."        
            try:
                _name = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.detail-conf-txt-sty h1'))
                ).text
                if '\n' in _name:
                    EventName = str(_name).replace('\n', ' ')
                else:
                    EventName = _name
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                return EventName


        def event_date(self) -> Tuple[str, str]:
            "Scrapes and return event date."
            try:
                Eventdate = self.browser.find_elements(By.CSS_SELECTOR, '.col-md-5:nth-child(1)')
                if Eventdate == None:
                    return ''
                Eventdate = [(i.text).split('\n') for i in Eventdate]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                date_list = []
                location_list = []
                for i in Eventdate:
                    if i[0][-4:].strip() in '2014 2015 2016 2017 2018 2019 2020 2021': #past event
                        continue
                    else:
                        date_list.append(date_transformation(i[0]))
                        location_list.append(location(i[1]))
                return date_list, location_list


        def event_info(self) -> str:
            "Scrapes and return event info."
            try:
                eventinfo = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.detail-conf-txt-sty p+p'))
                ).text

                if eventinfo == '':
                    eventinfo = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.detail-conf-txt-sty p+p+p'))
                    ).text

                if '\n' in eventinfo:
                    Eventinfo = eventinfo.split('\n', 1)[0]
                else:
                    Eventinfo = eventinfo
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)                
            else:
                if Eventinfo == None:
                    return ''
                else:
                    return Eventinfo


        def event_ticketlist(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                _ticketlist = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.pricing_price_col'))
                ).text

            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
                return ''
            else:
                if str(_ticketlist) == 'None' or not _ticketlist or str(_ticketlist) == 'null' :
                    return ''
                else:
                    Event_ticketlist = ticket_fee(_ticketlist)
                    return [json.dumps(dict(type='paid', price=Event_ticketlist[1], currency=Event_ticketlist[0]))]


        def orgprofile(self) -> str:
            "Scrapes and return orgprofile."
            try:
                Event_orgprofile = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.left-cnt'))
                ).text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)                
            else:
                return Event_orgprofile


        def orgname(self, x:str) -> str:
            return x
            

        def sponsor(self, x:str) -> str:
            try:
                return x
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)                
                


        def orgweb(self, x:str) -> str:
            return x
                            

        def contact_mail(self) -> str:
            "Scrapes and return contact mail."
            try:
                Contact_mail = WebDriverWait(self.browser, 10).until(
                            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, '@informa'))
                ).text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)                
                
            else:
                return Contact_mail


        def speaker_list(self) -> str:
            "Scrapes and return speakerlist"
            try:
                speaker = driver.find_elements(By.CSS_SELECTOR, '.speakers_right_sect_width')
                if not speaker: # if list is empty
                    return ''

                if str(speaker) == 'None' or str(speaker) == 'null':
                    return ''

                speakerList = []
                for t in speaker:
                    i = (t.text).strip()

                    if '\n' in i:  # a name a title is present
                        i = str(i).split('\n')
                        temp_use = dict(name=i[0], title=i[1], link='')
                        speakerList.append(json.dumps(temp_use.copy(), ensure_ascii=False))
                    else:           # only a name is present
                        temp_use = dict(name=i, title='', link='')
                        speakerList.append(json.dumps(temp_use.copy(), ensure_ascii=False))
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)                
            else:
                return speakerList


        def back_page(self) -> NoReturn:
            "goes a page back"
            self.browser.back()

        def next_page(self) -> NoReturn:
            "Moves the page down and click next page"
            time.sleep(3)
            html = self.browser.find_element(By.TAG_NAME, 'html')
            html.send_keys(Keys.PAGE_DOWN)
            try:
                next = self.browser.find_element(By.CSS_SELECTOR, '.pagecurrent_one .event_cal_list_next_btn').get_attribute('href')
                driver.get(next)
                time.sleep(2)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)                
                return False
            else:
                return True


    with ScrapeEvent() as handler:
        " This context manager handles the ScrapeEvent() Class object and handles it teardown for any resource(s) used."
        try:
            handler.navigate_to_eventpage(home_url) 
        except Exception as e:
            error = '\n\n' + str(e)
            pass
            
        flag = True  # helps to check when NO more event with next_page() function
        while flag:
        # your code for getting the links of events page from list page and storing them in a list

            try:
                links = handler.listing_page_urls() 
            except Exception as e:
                error = '\n\n' + str(e)
                pass
        #end of first part
        

        #second part        
            count = 1
            for link in links:
                data_row = [] 
                try:
                    try:
                        """ checks if url is valid/not broken """
                        valid_url = requests.get(link)
                        if valid_url.status_code < 400:
                            pass
                        else:
                            continue

                    except Exception as e:
                        error = '\n\n' + str(e)
                        pass

                    try:
                        handler.refresh_page() # somethings a refresh might be needed if the past action was a either a back
                        handler.get_event(link) # get the event using `driver.get(url)``
                    except Exception as e:
                        error = '\n\n' + str(e)
                        pass

                    """The date function is placed early to check if date is not `past` AND `if date present in the page`, if not; continue to next url"""
                    sc_date = handler.event_date()
                    date_list = sc_date[0]
                    location_list = sc_date[1]


                    if not date_list and not location_list:
                        handler.back_page()  # the back click here is expensive in the loop, but required to keep our listing page for iteriating paginations
                        handler.refresh_page # pages somethings give `Resubmission Error`
                        continue
                    
                    try:
                        sc_url = handler.scrapped_url()
                        scrappedUrl = sc_url
                    except Exception as e:
                        error = '\n\n' + str(e)
                        scrappedUrl = ' '


                    # 2 BLOCK CODE: scraping attribute eventtitle
                    try:
                        sc_name = handler.event_name()
                        eventname = sc_name
                    except Exception as e:
                        error = '\n\n' + str(e)
                        eventname = ' '


                    # 5 BLOCK CODE: scraping attribute timing
                    try:
                        timing = ''
                    except Exception as e:
                        error = '\n\n' + str(e)
                        timing = ' '


                    # 6 BLOCK CODE: scraping attribute event_info
                    try:
                        sc_event_info = handler.event_info()
                        eventinfo = sc_event_info
                    except Exception as e:
                        error = '\n\n' + str(e)
                        eventinfo = ' '


                    # 7 BLOCK CODE: scraping attribute ticketlist
                    try:
                        sc_ticket_list = handler.event_ticketlist()
                        ticketlist = sc_ticket_list
                    except Exception as e:
                        error = '\n\n' + str(e)
                        ticketlist = ' '


                    # 8 BLOCK CODE: scraping attribute orgProfile
                    try:
                        sc_org_profile = handler.orgprofile()
                        orgProfile = sc_org_profile
                    except Exception as e:
                        error = '\n\n' + str(e)
                        orgProfile = ' '


                    # 9 BLOCK CODE: scraping attribute orgName
                    try:
                        orgName = 'Informa Connect'
                    except Exception as e:
                        error = '\n\n' + str(e)
                        orgName = ' '


                    # 10 BLOCK CODE: scraping attribute orgWeb
                    try:
                        orgWeb = sc_url
                    except Exception as e:
                        error = '\n\n' + str(e)
                        orgWeb = ' '

                    # 11 BLOCK CODE: scraping attribute logo
                    logo = ''

                    # 12 BLOCK CODE: scraping attribute sponsor
                    try:
                        sc_sponsor = handler.sponsor('')
                        sponsor = sc_sponsor
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


                    # 19 BLOCK CODE: scraping attribute event_website
                    try:
                        event_website = sc_url
                    except Exception as e:
                        error = '\n\n' + str(e)
                        event_website = ' '


                    # 21 BLOCK CODE: scraping attribute ContactMail
                    try:
                        sc_contact_mail = handler.contact_mail()
                        ContactMail = [json.dumps(sc_contact_mail)]
                    except Exception as e:
                        error = '\n\n' + str(e)
                        contactMail = ' '


                    # 22 BLOCK CODE: scraping attribute Speakerlist
                    try:
                        sc_speaker_list = handler.speaker_list()
                        Speakerlist = sc_speaker_list
                    except Exception as e:
                        error = '\n\n' + str(e)
                        Speakerlist = ' '


                # 3 BLOCK CODE: scraping attribute startdate and enddate
                #  
                    """ This code blocks accounts for multiple events by `DATE` in each eventpage, the date function has been called earlier"""

                    if len(date_list) == 1:
                        """if event is singular"""
                        startdate = date_list[0][0]
                        enddate = date_list[0][1]

                    # 16 BLOCK CODE: scraping attribute city
                        try:
                            if location_list[0] == 'ONLINE':
                                city = ''
                            else:
                                city = location_list[0][0]
                        except Exception as e:
                            error = '\n\n' + str(e)
                            city = ' '


                        # 17 BLOCK CODE: scraping attribute country
                        try:
                            if location_list[0] == 'ONLINE':
                                country = ''
                            else:
                                country = location_list[0][1]
                        except Exception as e:
                            error = '\n\n' + str(e)
                            country = ' '


                        # 18 BLOCK CODE: scraping attribute venue
                        venue = ''


                        # 20 BLOCK CODE: scraping attribute googlePlaceUrl  
                        try:
                            if location_list[0] == 'ONLINE':
                                googlePlaceUrl = ''
                            else:
                                # Infromaconnect only gives country and city    
                                googlePlaceUrl = ''
                        except Exception as e:
                            error = '\n\n' + str(e)
                            googlePlaceUrl = ' '

                        
                        # 23 BLOCK CODE: scraping attribute online_event
                        try:
                            if location_list[0] == 'ONLINE':
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


                    else:
                        """if event is more than one"""
                        for i in range(len(date_list)):
                            startdate = date_list[i][0]
                            enddate = date_list[i][1]

                            # 16 BLOCK CODE: scraping attribute city
                            try:
                                if location_list[i] == 'ONLINE':
                                    city = ''
                                else:
                                    city = location_list[i][0]
                            except Exception as e:
                                error = '\n\n' + str(e)
                                city = ' '


                            # 17 BLOCK CODE: scraping attribute country
                            try:
                                if location_list[i] == 'ONLINE':
                                    country = ''
                                else:
                                    country = location_list[i][1]
                            except Exception as e:
                                error = '\n\n' + str(e)
                                country = ' '
            
                            # 18 BLOCK CODE: scraping attribute venue
                            venue = ''


                            # 20 BLOCK CODE: scraping attribute googlePlaceUrl
                            try:
                                if location_list[i] == 'ONLINE':
                                    googlePlaceUrl = ''
                                else:
                                    googlePlaceUrl = ''         # informaconnect event has no venue
                            except Exception as e:
                                error = '\n\n' + str(e)
                                googlePlaceUrl = ' '

                            
                            # 23 BLOCK CODE: scraping attribute online_event
                            try:
                                if location_list[i] == 'ONLINE':
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


                    handler.back_page()  # the back click here is expensive in the loop, but required to keep our listing page for iteriating paginations
                    handler.refresh_page # pages somethings give `Resubmission Error`

                except Exception as e:
                    print(e)
                    error += '\n' + str(e) + handler.error_msg_from_class
                    continue

            flag = handler.next_page()


except Exception as e:
    print(e)
    error = '\n\n' + str(e)

#to save status
GlobalFunctions.update_scrpping_execution_status(file_name, error)

# BYE!!!.

