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
from typing import Any, Union

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
import warnings

import requests
from GlobalFunctions import GlobalFunctions
from GlobalVariable import GlobalVariable

warnings.filterwarnings("ignore")

#*******************************************************************************************************************
def date_transforamtion(start:str, end:str) -> tuple:

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
        """ the codebase design uses a Class with it Methods as function scraping singular data(some more,
        in the case of going inside the page just once). It returns the data to a it caller which is handled by a context manager"""

        browser: WebDriver = driver
        wait_5sec: WebDriverWait = WebDriverWait(browser, 5)
        error_msg_from_class: str = ''

        def __enter__(self):
            return self

        def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
            self.browser.quit()

        def get_events(self, url: str) -> int:
            try:
                self.browser.get(url)
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                try:
                    all_event = self.browser.find_elements(By.CSS_SELECTOR, '.event')
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                else:
                    return len(all_event)


        def click_event(self, index:int) -> None:
            try:
                time.sleep(1)
                all_events = self.browser.find_elements(By.CSS_SELECTOR, '.event')
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                page = all_events[index]
                try:
                    ActionChains(self.browser).move_to_element(page).click(on_element=page).perform()
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)


        def event_name(self) -> str:
            try:
                sc_event_name = self.browser.find_element(By.CSS_SELECTOR, '#ac-event-title').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                return sc_event_name


        def event_date(self) -> tuple:
            try:
                sc_event_start_date = self.browser.find_element(By.CSS_SELECTOR, '.start strong').text
                sc_event_end_date =  self.browser.find_element(By.CSS_SELECTOR, '.end').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                rf_date = date_transforamtion(sc_event_start_date, sc_event_end_date)
                if rf_date:
                    return rf_date
                else:
                    return '', ''

        
        def event_info(self) -> str:
            try:
                sc_event_info = self.browser.find_element(By.CSS_SELECTOR, '.details p').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                return ' '.join(sc_event_info.split('.')[:2])


        def event_timing(self) -> json:
            try:
                sc_event_timing = self.browser.find_element(By.CSS_SELECTOR, '.end').text
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                match = re.search('([\d\d]+:\d\d \w\w)\s+(\(\w\w\w\))', sc_event_timing)
                if match:
                    return [
                            json.dumps(
                                dict(type='general',
                                    Start_time=match.group(1),
                                    end_time='',
                                    timezone=match.group(2).replace('(', '', 1).replace(')', '', 1),
                                    days='all'))
                        ]
                else:
                    return ''


        def event_ticket_list(self) -> json:
            try:
                soup = bs(self.browser.page_source,'html.parser')
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
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



        def event_mode(self, sc_event_name:str) -> str:

            if 'online' in sc_event_name.lower() or 'virtual' in sc_event_name.lower() or 'webinar' in sc_event_name.lower():
                return 'ONLINE'

            try:
                mode1 = self.browser.find_element(By.CSS_SELECTOR, '.o-details-block__details-info div').text
            except NoSuchElementException or Exception as e:
                mode1 = ''
                self.error_msg_from_class += '\n' + str(e)
                try:
                    all_text = self.browser.find_element(By.CSS_SELECTOR, '.details.inner-content').text
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                else:
                    if 'online' in all_text.lower() or 'virtual' in all_text.lower() or 'webinar' in all_text.lower():
                        return 'ONLINE'
                    else:
                        try:
                            mode2 = self.browser.find_element(By.CSS_SELECTOR, '.details.inner-content h5').text
                        except Exception as e:
                            self.error_msg_from_class += '\n' + str(e)
                        else:
                            rf_mode2 = mode2.split('|')[1].strip()
                            if len(rf_mode2) < 21:
                                return '', rf_mode2, ''
                            venue, city = rf_mode2.split(',')[0], rf_mode2.split(',')[1]
                            return venue, city, ''
            else:
                if mode1:
                    rf_mode1 = mode1.split(',')
                    location = rf_mode1[0].replace('\n', '').strip(), rf_mode1[1].replace('\n', ' ').strip()
                    venue = location[0]
                    match =  re.search('(.+\d+)(.+)', location[1])
                    city, country = match.group(1), match.group(2)
                    return venue, city, country
            

        def event_speakerlist(self):
            try:
                sc_1  = self.browser.find_element(By.CSS_SELECTOR, '.member').text
            except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    return ''
            else:
                name = sc_1.split('\n')[0]
                title = ' '.join(sc_1.split('\n')[1:])
                return json.dumps([dict(name=name, title=title, link='')])


        def google_map_url(self, search_word: str) -> str:
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



        def back_page(self) -> None:
            self.browser.back()
            time.sleep(0.5)



    base_url = 'https://www.aaspa.org/events/?&Page='

    with ScrapeEvent() as handler:
        """ This context manager handles the ScrapeEvent() Class object and instantiates it caller varaibles"""
        handler.browser.implicitly_wait(10)

        try:
            events = handler.get_events(base_url)
        except NoSuchElementException or TimeoutException or Exception as e:
            error += '\n' + str(e)
    # end of first part

    # second part
        for i in range(events):
            try:
                handler.click_event(i)
                time.sleep(1)

                # 1 BLOCK CODE: scraping attribute scrappedUrl
                scrappedUrl = handler.browser.current_url

                # 2 BLOCK CODE: scraping attribute eventname
                try:
                    eventname = handler.event_name()
                except Exception as e:
                    error += '\n' + str(e)
                    eventname = ''
                        
                # 3 & 4 BLOCK CODE: scraping attribute startdate and enddate
                try:
                    date = handler.event_date()
                    startdate = date[0]
                    enddate = date[1]
                except Exception as e:
                    error += '\n' + str(e)
                    startdate = ''
                    enddate = ''
                

                # 5 BLOCK CODE: scraping attribute timing
                try:
                    timing = handler.event_timing()
                except Exception as e:
                    error += '\n' + str(e)
                    timing = ''

                # 6 BLOCK CODE: scraping attribute event_info
                try:
                    eventinfo = handler.event_info()
                    if not eventinfo:
                        eventinfo = f'Theme: {eventname.title()} + {startdate} - {enddate}'
                except Exception as e:
                    error += '\n' + str(e)
                    eventinfo = ''

                # 7 BLOCK CODE: scraping attribute ticketlist
                try:
                    ticketlist = handler.event_ticket_list()
                except Exception as e:
                    error += '\n' + str(e)
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
                    googlePlaceUrl = ''

                # 21 BLOCK CODE: scraping attribute ContactMail
                ContactMail = ''

                # 22 BLOCK CODE: scraping attribute Speakerlist
                try:
                    Speakerlist = handler.event_speakerlist()
                except Exception as e:
                    error += '\n' + str(e)
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
                handler.back_page()

            except Exception as e:
                print(e)
                error += '\n' + str(e) + handler.error_msg_from_class
                print('get here sometimes too')
                continue

except Exception as e:
    error += '\n' + str(e)
    print(error)

#to save status
GlobalFunctions.update_scrpping_execution_status(file_name, error)
