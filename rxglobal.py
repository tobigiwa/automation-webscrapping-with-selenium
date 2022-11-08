
# -*- coding: utf-8 -*-
"""
@author: ChewingGumKing_OJF
"""
import json
#loads necessary libraries
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import NoReturn, Union

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

#*******************************************************************************************************************
sys.path.insert(0, os.path.dirname(__file__).replace('parsing-new-script','global-files/'))

import json
#*******************************************************************************************************************
import warnings

import requests
from GlobalFunctions import *
from GlobalVariable import *

warnings.filterwarnings("ignore")


home_url = 'https://rxglobal.com/'

def date_transformation(s:str) -> tuple:
    """ handling date transfromation to required format"""
    date_format = '%d %B %Y'
    if 'th' in s:
        s = s.replace('th', '')
    if 'nd' in s:
        s = s.replace('nd', '')
    if 'st' in s:
        s = s.replace('st', '')
    if 'rd' in s:
        s = s.replace('rd', '')
    if 'Augu' in s:
        s = s.replace('Augu', 'August', 1)

    if '-' in s:
        v = s.split(' - ')
        month_year = v[1].split(' ', 1)[1].strip()
        year = month_year[-4:]
        v[0] += f' {year}' if len(v[0].split(' ', 1)) > 1 else f' {month_year}'
        return datetime.strptime(v[0],date_format).strftime('%Y-%m-%d'), datetime.strptime(v[1],date_format).strftime('%Y-%m-%d')
    else:
        return datetime.strptime(s,date_format).strftime('%Y-%m-%d'), datetime.strptime(s,date_format).strftime('%Y-%m-%d')


def location(s:str) -> str:
    """ handling location transfromation to required format"""

    mapping_table = s.maketrans('»', '>') # faster method to remove and insert in a string
    s = s.translate(mapping_table)
    s = s.split('>')
    del s[0]

    return s

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
        """ 
        The codebase design uses a single Class( dataclass) with it Methods as function scraping singular data (some more though).
        Returns the "self" to a it caller which is handled by a context manager.
        """

        browser: WebDriver = driver
        wait_5sec: WebDriverWait = WebDriverWait(browser, 5)

        def __enter__(self) -> NoReturn:
            "Handles the contex manager."
            return self


        def __exit__(self, exc_type=None, exc_value=None, exc_tb=None) -> NoReturn:
            "Returns a list of all urls"
            self.browser.quit()


        def navigate_to_listing_page(self, url:str) -> NoReturn:
            """gets us from the home page to the event listing page, runs once"""
            try:
                self.browser.implicitly_wait(5)
                self.browser.get(url)
                action_chain = ActionChains(self.browser)

                time.sleep(2) # cookie pop-up is very slow
                try:
                    self.wait_5sec.until(
                        EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))
                    ).click()
                except Exception as e:
                    error = '\n\n' + str(e)
                    pass

                all_events = self.wait_5sec.until(
                    EC.presence_of_element_located((By.LINK_TEXT, 'Events')))

                action_chain.move_to_element(all_events).perform()

                find_all_events = self.wait_5sec.until(
                    EC.presence_of_element_located((By.LINK_TEXT, 'Find an event'))
                )
                find_all_events.click()
            except Exception as e:
                error = '\n\n' + str(e)
                pass


        def listing_page_urls(self) -> int:
            """Extract the length of events i.e 'hrefs' present, this is use in iterating"""
            try:
                event_boxes_urls = self.browser.find_elements(By.CSS_SELECTOR, '.col-xl-3')
            except Exception as e:
                error = '\n\n' + str(e)
                pass
            else:
                return len(event_boxes_urls)


        def scrapped_url(self, x:int) -> str:
            """ scrapes the url"""
            try:
                ScrappedUrl = self.wait_5sec.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f'.col-xl-3:nth-child({x}) > a'))
                    ).get_attribute('href')
            except Exception as e:
                error = '\n\n' + str(e)
                pass
            else:
                return ScrappedUrl


        def event_name(self, x:int) -> str:
            """event name"""
            try:
                EventName = self.wait_5sec.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f'.col-xl-3:nth-child({x}) .event-title'))
                    ).text
            except Exception as e:
                error = '\n\n' + str(e)
                pass
            else:
                return EventName


        def event_date(self, x:int) -> Union[tuple, str]:
            """event date, calls the date_transformation function"""
            try:
                date = self.wait_5sec.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f'.col-xl-3:nth-child({x}) .event-date'))
                    ).text
                if date == 'TBC': # as found for empty date
                    return 'no date'
            except Exception as e:
                error = '\n\n' + str(e)
            else:
                EventDate = date_transformation(str(date))
                return EventDate


        def event_info(self, x:int) -> str:
            "Scrapes and return event info"
            info = self.browser.find_element(By.CSS_SELECTOR, f'.col-xl-3:nth-child({x})').text
            info = info.replace('\n', ' ').replace('>', '').replace('»', '')
            return info


        def org_profile(self) -> str:
            "Return event info"
            profile = "We are in the business of building businesses so everyone can thrive whoever and wherever you are. Our flagship events will always be our pride and focus, but we're now building on these creating year-round communities with shared passions and purpose, designed to help businesses and people grow continually."
            profile = profile.replace('\n', ' ')
            return profile

        def org_name(self) -> str:
            "Return org_nmae"
            name = 'Rxglobal'
            return name


        def org_web(self) -> str:
            "Return org_web"
            web = 'https://rxglobal.com/'
            return web


        
        def event_sponsor(self, x:int) -> str:
            "Scrapes and returns event_sponsor"
            try:
                sponsor = self.wait_5sec.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f'.col-xl-3:nth-child({x}) > a'))
                    ).get_attribute('href')
                
                sponsor = str(sponsor).replace('http://www.', '').replace('https://www.', '').replace('.com', '').replace('html', '').replace('/', '').replace('http:', '').replace('https:', '').replace('www', '').replace('//', '').replace('?', ' ').replace('#', '').replace('_ga=2.196945388.1162053868.1659593808-2064319060.1659593808', '')
            except Exception as e:
                error = '\n\n' + str(e)
            else:
                return [json.dumps(sponsor)]


        def event_location(self, x:int) -> str:
            """event location, calls `location` fucntion"""
            try:
                online = self.wait_5sec.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f'.col-xl-3:nth-child({x}) .event-mode'))
                ).text

                if online == 'Hybrid' or online == 'Virtual':
                    return 'ONLINE'
                else:
                    locale = self.wait_5sec.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f'.col-xl-3:nth-child({x}) .event-location'))
                    ).text
                    EventLocation = location(locale)
            except Exception as e:
                error = '\n\n' + str(e)
                pass
            else:
                return EventLocation


        def event_venue(self, x:int) -> str:
            """ event venue, also checks event-mode"""
            try:
                online = self.wait_5sec.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f'.col-xl-3:nth-child({x}) .event-mode'))
                ).text

                if online == 'Hybrid' or online == 'Virtual':
                    return 'ONLINE'
                else:
                    EventVenue = self.wait_5sec.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f'.col-xl-3:nth-child({x}) .event-meta-location'))
                    ).text
                    return EventVenue
                    
            except Exception as e:
                error = '\n\n' + str(e)
                return ''


        def google_map_url(self,search_word) -> str:   
            """ this implementation of the Google serach function is neccesary because of the nature of the website"""

            if search_word == 'ONLINE':
                return 'ONLINE'

            curr_tab = self.browser.current_window_handle
            self.browser.switch_to.new_window('tab')

            try:
                def gu(luc):
                    google_url_for_location="https://www.google.com/search?q="+luc+"&oq="+luc+"&num=1"
                    time.sleep(randint(0,3))
                    driver.get(google_url_for_location)
                    time.sleep(4)
                    try:
                        google_map_url=driver.find_element("id",'lu_map').click()
                    except:
                        try:
                            google_map_url=driver.find_element("class name",'Xm7sWb').click()
                        except:
                            try:
                                google_map_url=driver.find_element("class name",'dirs').click()
                            except:
                                try:
                                    google_map_url=driver.find_element("class name",'GosL7d cYnjBd').click()
                                except:
                                    google_map_url=driver.find_element("class name",'Lx2b0d').click()
                    time.sleep(1)
                    google_map_url=driver.current_url
#                 print(google_map_url)
                    return(google_map_url)
        ######################################
                def get_google_map_url(location):
                    try:
                        return(gu(location))
                    except:
                        try:
                            return(gu(location))
                        except:
                            sha=location.split(',')
                            try:
                                return(gu(sha[-3]))
                            except:
                                try:
                                    return(gu(sha[-2]))
                                except:
                                    try:
                                        return(gu(sha[-1]))
                                    except Exception as e:
                                        print(location, "; url didn't go through")
                                        print(e)
                                        return("")
                map_url = get_google_map_url(search_word)
            except Exception as e:
                error = '\n\n' + str(e)
            else:
                self.browser.close()
                self.browser.switch_to.window(curr_tab)
                return map_url                
                
        def contact_mail(self) -> str:
            "Returns contact_mail"
            mail = 'rxinfo@reedexpo.co.uk'
            return json.dumps([mail])


        def next_page(self):
            """runs at the end of  each length-of-event-iteration on each page and clicks on `NEXT`, `element_to_be_clickable`
            has to be employed as the very last page DOM still has `NEXT` but of zero width and height. This behavior would be detectable
            and return `False` to stop scraping iteration otherwise  `True` to continue to the next page
            """
            time.sleep(1.5) # cookie pop somethings slow
            try:
                cookie_pop_up = self.wait_5sec.until(
                        EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))
                    )
                cookie_pop_up.click()
            except Exception as e:
                error = '\n\n' + str(e)
                pass
            try:
                time.sleep(1.5) # ensures program rest before before detecting
                self.wait_5sec.until( 
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.pager__item--next a'))
                ).click()
                time.sleep(2)
                return True
            except Exception as e:
                error = '\n\n' + str(e)
                return False


    with ScrapeEvent() as handler:
        " This context manager handles the ScrapeEvent() Class object and handles it teardown for any resource(s) used."

        handler.navigate_to_listing_page(home_url)

        flag = True # helps to check when NO more event with next_page() function
        while flag:
            # your code for getting the links of events page from list page and storing them in a list

            try:
                links = handler.listing_page_urls()
            except Exception as e:
                error = '\n\n' + str(e)
                pass
        #end of first part


        #second part 
                
            for i in range(links):
                try:
                    index = i + 1 # for accessing individual css child element
                    try:
                        sc_url = handler.scrapped_url(index)
                    except Exception as e:
                        error = '\n\n' + str(e)
                        scrappedUrl = ''

                    scrappedUrl = 'https://rxglobal.com/events'

                    try:
                        """ checks if url is valid/not broken """
                        valid_url = requests.get(sc_url)
                        if valid_url.status_code < 400:
                            pass
                        else:
                            continue

                    except Exception as e:
                        error = '\n\n' + str(e)
                        pass


                    # 2 BLOCK CODE: scraping attribute eventtitle
                    try:
                        sc_name = handler.event_name(index) 
                        eventname = sc_name
                    except Exception as e:
                        error = '\n\n' + str(e)
                        eventname = ''


                    # 3 BLOCK CODE: scraping attribute startdate and enddate
                    try:
                        sc_date = handler.event_date(index)

                        if sc_date == 'no date':
                            continue

                        if not sc_date[0]  and not sc_date[1]:
                            continue

                        else:
                            startdate = sc_date[0]
                            enddate = sc_date[1]
                    except Exception as e:
                        error = '\n\n' + str(e)
                        startdate = ''
                        enddate = ''


                    # 5 BLOCK CODE: scraping attribute timing
                    try:
                        timing = ''
                    except Exception as e:
                        error = '\n\n' + str(e)
                        timing = ''


                    # 6 BLOCK CODE: scraping attribute event_info
                    try:
                        eventinfo = handler.event_info(index)
                    except Exception as e:
                        error = '\n\n' + str(e)
                        eventinfo = ''


                    # 7 BLOCK CODE: scraping attribute ticketlist
                    ticketlist = ''  


                    # 8 BLOCK CODE: scraping attribute orgProfile
                    orgProfile = handler.org_profile()

                    # 9 BLOCK CODE: scraping attribute orgName
                    orgName = handler.org_name()

                    # 10 BLOCK CODE: scraping attribute orgWeb
                    orgWeb = handler.org_web()

                    # 11 BLOCK CODE: scraping attribute logo
                    logo = ''


                    # 12 BLOCK CODE: scraping attribute sponsor
                    try:
                        #sponsor = handler.event_sponsor(index)
                        sponsor = ''
                    except Exception as e:
                        error = '\n\n' + str(e)
                        sponsor = ''


                    # 13 BLOCK CODE: scraping attribute agendalist
                    agendalist = ''


                    #14 BLOCK CODE: scraping attribute type
                    type = ''
                    #15 BLOCK CODE: scraping attribute category
                    category = ''


                    # 16 BLOCK CODE: scraping attribute city
                    try:
                        sc_location = handler.event_location(index)
                        if sc_location == 'ONLINE':
                            city = ''
                        else:
                            city = sc_location[1]
                    except Exception as e:
                        error = '\n\n' + str(e)
                        city = ''


                    # 17 BLOCK CODE: scraping attribute country
                    try:
                        sc_location = handler.event_location(index)
                        if sc_location == 'ONLINE':
                            country = ''
                        else:
                            country = sc_location[0]
                    except Exception as e:
                        error = '\n\n' + str(e)
                        country = ''
                        
                        # 18 BLOCK CODE: scraping attribute venuev
                    try:
                        sc_venue = handler.event_venue(index)
                        if sc_venue == 'ONLINE':
                            venue = ''
                        else:
                            venue = sc_venue
                    except Exception as e:
                        error = '\n\n' + str(e)
                        venue = ''


                    # 19 BLOCK CODE: scraping attribute event_website
                    event_website = sc_url

                    # 20 BLOCK CODE: scraping attribute googlePlaceUrl
                    try:
                        if sc_location == 'ONLINE' or sc_venue == '' or not sc_venue:
                            googlePlaceUrl = ''
                        else:
                            sc_search_word = f'{sc_venue} {sc_location[1]} {sc_location[0]}'
                            gg_map = handler.google_map_url(sc_search_word)
                            googlePlaceUrl = gg_map
                    except Exception as e:
                        error = '\n\n' + str(e)
                        googlePlaceUrl = ''


                    # 21 BLOCK CODE: scraping attribute ContactMail
                    ContactMail = handler.contact_mail()

                    # 22 BLOCK CODE: scraping attribute Speakerlist
                    Speakerlist = ''

                    # 23 BLOCK CODE: scraping attribute online_event
                    try:
                        if sc_location == 'ONLINE':
                            online_event = 1
                        else:
                            online_event =  0 

                    except Exception as e:
                        error = '\n\n' + str(e)
                        online_event = ''

                    data_row = [scrappedUrl, eventname, startdate, enddate, timing, eventinfo, ticketlist,
                                orgProfile, orgName, orgWeb, logo, sponsor, agendalist, type, category, city,
                                country, venue, event_website, googlePlaceUrl, ContactMail, Speakerlist, online_event]
                    
                    GlobalFunctions.appendRow(file_name,  data_row)

                except Exception as e:
                    print(e)
                    error = '\n\n' + str(e)
                    continue
                    
            flag = handler.next_page()
            time.sleep(2) #allow for next-page to reload

except Exception as e:
    print(e)
    error = '\n\n' + str(e)

#to save status
GlobalFunctions.update_scrpping_execution_status(file_name, error)
