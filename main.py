from datetime import datetime
import re
import numpy as np
import pandas as pd
from pandas import DataFrame
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

relevant_comps = ["Grand Prix", "Grand Slam", "Masters", "World Senior Championship", "World Championships Senior",
                  "World Judo Championships Seniors"]


def get_competitions():
    start_comp = 1341  # first comp after 2016 Rio Olympics
    end_comp = 2239  # last comp before Tokyo Olympics
    comps = []
    start_dates = []
    end_dates = []
    countries = []
    comp_id = []
    while start_comp <= end_comp:
        driver.get(f'https://judobase.ijf.org/#/competition/profile/{start_comp}/statistics')
        try:
            WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, '//div[@class="well"]')))
        except TimeoutException:
            start_comp += 1
            continue

        except UnexpectedAlertPresentException:
            start_comp += 1
            continue

        comp_info = (driver.find_element(By.XPATH, '//div[@class="well"]')).text
        if any([x in comp_info for x in relevant_comps]):
            comp_list = re.split('\n|From | to | in ', comp_info)
            total_list = [i for i in comp_list if i]
            comps.append(total_list[0])
            start_dates.append(total_list[1])
            end_dates.append(total_list[2])
            countries.append(total_list[3])
            comp_id.append(start_comp)
        start_comp += 1

    competitions = pd.DataFrame(np.column_stack([comp_id, comps, countries, start_dates, end_dates]),
                                columns=['comp_id', 'competition', 'host_country', 'start_date', 'end_date'])
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    competitions.set_index('comp_id', inplace=True)

    discard = ["Kata"]
    competitions = competitions[~competitions.competition.str.contains('|'.join(discard))]
    competitions['start_date'] = pd.to_datetime(competitions['start_date'], format='%Y-%m-%d')
    competitions = competitions.loc[(competitions['start_date'] > '2016-09-22')]

    return competitions

    #  to save as CSV file
    #  competitions.to_csv('competitions.csv')


# get_competitions()

tournaments = get_competitions()


def get_players():
    df = tournaments
    start_div = 1  # start at -60kg
    end_div = 14  # end at +78 kg
    player_ids = []
    player_names = []
    player_countries = []
    player_sex = []

    for i in df.index:
        while start_div <= end_div:
            driver.get(f'https://judobase.ijf.org/#/competition/profile/{i}/competitors/{start_div}')
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//div[@class="js-categories"]')))
            players = (driver.find_elements(By.XPATH, '//tr[@data-id_person]'))
            names = (driver.find_elements(By.XPATH, '//td[@data-name="full_name"]'))
            countries = (driver.find_elements(By.XPATH, '//span[@title]'))
            for p_id in players:
                player_ids.append(p_id.get_attribute('data-id_person'))
                if start_div <= 7:
                    player_sex.append('Male')
                else:
                    player_sex.append('Female')
            for name in names:
                player_names.append(name.text)
            for country in countries:
                if country.get_attribute('title') == "Russian Judo Federation":
                    player_countries.append("Russian Federation")
                elif country.get_attribute('title') == "IJF":
                    player_countries.append("IJF Refugee Team")
                else:
                    player_countries.append(country.get_attribute('title'))
            start_div += 1
            if start_div > end_div:
                start_div = 1
                break

    athletes: DataFrame = pd.DataFrame(np.column_stack([player_ids, player_names, player_countries, player_sex]),
                                       columns=['player_id', 'athlete_name', 'nationality', 'sex'])

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    athletes.set_index('player_id', inplace=True)

    athletes = athletes.groupby(athletes.index).first()

#     athletes.to_csv('athletes.csv')

    return athletes


# get_players()
