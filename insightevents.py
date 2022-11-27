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
import regex

#*******************************************************************************************************************
sys.path.insert(
    0,
    os.path.dirname(__file__).replace('parsing-new-script', 'global-files/'))

#*******************************************************************************************************************
import warnings

from GlobalFunctions import GlobalFunctions
from GlobalVariable import GlobalVariable

warnings.filterwarnings("ignore")

#*******************************************************************************************************************
def split_names(text):
    splitted = text.text.split('\n')
    if len(splitted) == 1:
        splitted.append('')
    return splitted

def date_transformation(date: str) -> Tuple[str, str]:
    match = re.search(r'(\d{1,2})-(\d{1,2})\s*(\w+)\s*(\d{4})', date)
    if match:
        change = lambda exact: datetime.strptime(exact, '%d %B %Y').strftime('%Y-%m-%d')
        return tuple(map(lambda no: change(' '.join(match.group(no, *(3, 4)))), [1, 2]))
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


        def get_events(self, url: str) -> List[str]:
            "Returns a list of all urls"
            try:
                self.browser.get(url)
                time.sleep(1)
                self.dispatch('#cookie_action_close_header').click()
            except:
                pass
            try:
                all_url = [each.get_attribute('href') for each in self.dispatchList('.pt-cv-ifield>h4>a')]
                all_title = [each.text for each in self.dispatchList('.pt-cv-ifield>h4>a')]
                all_date = map(date_transformation, [each.text for each in self.dispatchList('.pt-cv-ifield .pt-cv-ctf-value>strong')])
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                return list(zip(all_url, all_title, all_date))

        def get_dates(self) -> List[Tuple[str, str]]:
            "TScrapes and returns a list of date"
            try:
                all_dates = [each.text for each in self.dispatchList('.event-date')]
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            else:
                return list(map(date_transformation, all_dates))
        

        def get_event(self, url: str) -> NoReturn:
            "Get a singualr event from a list of all events"
            try:
                self.browser.get(url)
                time.sleep(1)
                self.dispatch('#cookie_action_close_header').click()
            except Exception as e:
                self.error_msg_from_class += '\n' + str(e)
            
        
        
        def event_info(self) -> str:
            "Scrapes and return event info."
            try:
                sc_event_info = self.dispatch('.fusion-title-1').text 
            except Exception as e:
                try:
                    sc_event_info = self.dispatch('#ut_inner_column_6380cbc8c88fb p').text
                    sc_event_info = re.findall(r'([^\?]+\?)', sc_event_info)
                except:
                    self.error_msg_from_class += '\n' + str(e)
                else:
                    return sc_event_info[0]
            else:
                return sc_event_info


        def event_ticket_list(self) -> json:
            "Scrapes and return a JSONified format of event timing."
            try:
                price_t_1 = self.dispatch(".fusion-text tbody .row-1 .column-2").text
                price_v_1 = self.dispatch(".fusion-text tbody .row-2 .column-2").text.split(' ')
            except Exception as e:
                try:
                    price_t_1 = self.dispatch(".row-2 .column-1").text
                    price_v_1 = self.dispatch(".row-2 .column-2").text.split(' ')
                    price_t_2 = self.dispatch(".row-3 .column-1").text
                    price_v_2 = self.dispatch(".row-3 .column-2").text.split(' ')
                except:
                    self.error_msg_from_class += '\n' + str(e)
                else:
                    return [
                    {'type':price_t_1, 'price':price_v_1[0], 'currency':price_v_1[1]},
                    {'type':price_t_2, 'price':price_v_2[0], 'currency': price_v_2[1]}]
            else:
                return [
                    {'type':price_t_1, 'price':price_v_1[0], 'currency':price_v_1[1]}]

        def event_mode(self) -> List[str]:
            "Scrapes and return event venue "
            try:
                location = self.dispatch(".link-type-text>.content-container p").text.split('\n')
            except Exception as e:
                try:
                    location = self.dispatch("#slider-1-slide-1-layer-1").text.split(' | ')[1]
                except:
                    self.error_msg_from_class += '\n' + str(e)
                else:
                    return ['', '', location]
            else:
                return location
                    

        def contactmail(self) -> json:
            "Scrapes and return a JSONified format of event contact email(s)."
            try:
                soup = bs(self.browser.page_source,'lxml')
                rex=r"""(?:[a-z0-9!#$%&'+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'+/=?^_`{|}~-]+)|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])")@(?:(?:[a-z0-9](?:[a-z0-9-][a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-][a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
                ma=[regex.search(rex,fxc).group() for fxc in ' '.join(soup.body.get_text(separator=' ').split()).lower().split() if regex.search(rex,fxc) != None]
                mal=[dc[:-1] if dc.endswith('.') else dc for dc in ma]
                con = list(dict.fromkeys(mal+ ['info@insightevents.se']))
                if con==[] or con=='':
                    con=['info@insightevents.se']
            except:
                con = ['info@insightevents.se']
            return con

        def event_speakerlist(self) -> json:
            "Scrapes and return a JSONified format of event speaker_list."
            try:
                speaker_list = list(map(split_names, self.dispatchList('.fusion-one-fourth p[style="text-align: center;"]')))
                speaker_list = speaker_list[1:]
                if speaker_list == []:
                    raise IndexError
            except Exception as e:
                try:
                    speaker_list = list(map(split_names, self.dispatchList('.bklyn-team-member-info')))
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                else:
                    return list(map(lambda a: {'name':a[0], 'title': a[1], 'link': ''}, speaker_list))
            else:
                return list(map(lambda a: {'name':a[0], 'title': a[1], 'link': ''}, speaker_list))



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

            else:
                self.browser.close()
                self.browser.switch_to.window(curr_tab)
                return map_url


    base_url = 'https://insightevents.se/events/'

    with ScrapeEvent() as handler:
        " This context manager handles the ScrapeEvent() Class object and handles it teardown for any resource(s) used."
        handler.browser.implicitly_wait(10)
        try:
            all_events = handler.get_events(base_url)
        except NoSuchElementException or TimeoutException or Exception as e:
            error += '\n' + str(e)
    # end of first part

    # second part
        for i in all_events:

            # if i[0] == 'https://insightevents.se/events/battery-tech-for-ev/':
            #     continue
            try:
                try:
                    handler.get_event(i[0])
                    time.sleep(1)
                except Exception as e:
                    error += '\n' + str(e)

                # 1 BLOCK CODE: scraping attribute scrappedUrl
                scrappedUrl = handler.browser.current_url

                # 2 BLOCK CODE: scraping attribute eventname
                try:
                    eventname = i[1]
                except Exception as e:
                    error += '\n' + str(e)
                    eventname = ''

                # 3 & 4 BLOCK CODE: scraping attribute startdate and enddate
                try:
                    startdate = i[2][0]
                    enddate = i[2][1]
                except Exception as e:
                    error += '\n' + str(e)
                    startdate = ''
                    enddate = ''
                
            
                # 5 BLOCK CODE: scraping attribute timing
                try:
                    timing =''
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
                    if ticketlist:
                        ticketlist = json.dumps(ticketlist, ensure_ascii=False)
                    else: ticketlist = ''
                except Exception as e:
                    error += '\n' + str(e)
                    ticketlist = ''

                # 8 BLOCK CODE: scraping attribute orgProfile
                orgProfile = 'Insight Events Sweden AB (tidigare Informa IBC Sweden) startade sin verksamhet 1994 och genomför årligen ett flertal mässor, konferenser, kurser och utbildningar på den svenska marknaden. Våra tusentals deltagare är beslutsfattare från både privata näringslivet och offentlig sektor. Målsättningen är att ge våra deltagare ny och utvecklande kunskap med de mest kända experterna inom respektive område. Våra produkter erbjuder också möjlighet att personligen möta potentiella kunder och knyta nya affärskontakter.'

                # 9 BLOCK CODE: scraping attribute orgName
                orgName = 'Insight Events'

                # 10 BLOCK CODE: scraping attribute orgWeb
                orgWeb = 'https://insightevents.se/'

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
                    mode = handler.event_mode()
                except Exception as e:
                    error += '\n' + str(e)

                # 16, 17 & 18 BLOCK CODE: scraping attribute city, country, venue
                try:
                    if isinstance(mode, (tuple, list)):
                        venue = f'{mode[0]} {mode[1]}'
                        city = mode[2]
                        country = ''
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
                    if venue:
                        sc_search_word = f'{venue}'
                        googlePlaceUrl = handler.google_map_url(sc_search_word)
                    else:
                        googlePlaceUrl = ''
                except Exception as e:
                    error += '\n' + str(e)
                    googlePlaceUrl = ''

                # 21 BLOCK CODE: scraping attribute ContactMail
                try:
                    ContactMail = json.dumps(handler.contactmail(), ensure_ascii=False)
                except Exception as e:
                    error += '\n' + str(e)
                    ContactMail = ''

                # 22 BLOCK CODE: scraping attribute Speakerlist
                try:
                    Speakerlist = handler.event_speakerlist()
                    Speakerlist = json.dumps(Speakerlist, ensure_ascii=False)
                    if Speakerlist is None:
                        Speakerlist = ''
                except Exception as e:
                    error += '\n' + str(e)
                    Speakerlist = ''

                # 23 BLOCK CODE: scraping attribute online_event
                try:
                    if (venue or city):
                        online_event = 0
                    else:
                        online_event = 1
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

            except Exception as e:
                error += '\n' + str(e) + handler.error_msg_from_class
                continue

except Exception as e:
    error += '\n' + str(e)
    print(error)

#to save status
GlobalFunctions.update_scrpping_execution_status(file_name, error)


# BYE!!!.

