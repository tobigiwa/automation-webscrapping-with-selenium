# Webscraping (with Selenium and BeautifulSoup) and Automation Using Python

## Project Description

This project consist of mutiple python files demonstrating elaborate webscraping programs that spans mutilple webpages using `Selenium` and `BeautifulSoup` with `Python`. The code design is rooted in making automation elegant with little hassle on re-application on any other needs. The codebase is well documentated, logged with the Python `Logging` module and fully type-annotated using the Python3.6> `Typing Module`, i.e

> **from typing import List, Dict, Optional, Union, Tuple, Callable, Sequence, Noreturn**

> **remark_on_job: str = 'Good'**

> **container: List[Dict] = []**

> **def func(num: int, input: Optional[Callable] = None, Union[Sequence, int]) -> NoReturn: ...**

Interested in learning the Python Module?, check out this [Real Python Guide.](https://realpython.com/python-type-checking/)

## Project Objective

Automating and designing a maintainable codebase for scraping mutiple webpages using Selenium and BeautifulSoup with python. `Maintainable` is the inspiration for this codebase design, hence why the Python `Logging Module` is also included.

**So, ideally, the program should be splitted in four scripts, but since my client for this job requested them in single script, it in one now. You can divide and resolve import :+1: :+1:.**

The basic schema design is stated below:

- A script(soup.py) of a Python Class with it only attribute as the browser driver and **it methods are function doing a singular scraping job**.

- A script(cooking.py) with a context manager variable calling each function and appending the scrape data to a list of dictionaries.

- A script(chopping.py) responsible for managing extra transformation needed for the scrape data.

- A script(create_log.py) to create logging for our code.

See, how maintainabilitiy is easy :+1: :+1:.

**NB:** Not all scripts are logged, so i'll recommend taking a look at aaspa.py, rhemda.py or starconferences.py.

## Running the script

Run `pip install -r requirement.txt` in your activated virtualenv to have all needed dependencies.

The scraping are configured to run headless (i.e without a broswer GUI), but you can comment out it out.

Run `python <python script> <tsv filename> <browser port> ` to execute the program or however you have rearranged yours.

If you prefer Pandas (as i did, not my client though), store your scraped data in dictionary format,a list of dictionaries is convertible into a Pandas Dataframe which is then written to tab seperated file format. If yow however decide to run the any of the python files, it expected that the data in it tsv would be different from your cuurent run.

I do hope my code brings good readability. :+1: :+1:
