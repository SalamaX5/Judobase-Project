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

def get_weights():
    player_id = []
    weight_cat = []
    start_time = []
    end_time = []
    df1 = athletes
    for i in df1.index:
        df2 = tournaments
        driver.get(f'https://judobase.ijf.org/#/competitor/profile/{i}/results')
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//td[@class=" sorting_1"]')))

        comp_col = driver.find_elements(By.XPATH, '//*[@data-table_name="results"]/tbody/tr/td[3]')

        results = []
        row = 1
        curr_weight = ''
        curr_date = ''
        curr_comp = ''

        for c in comp_col:
            date_col = driver.find_element(By.XPATH, f'//*[@data-table_name="results"]/tbody/tr[{row}]/td[2]')
            weight_col = driver.find_element(By.XPATH, f'//*[@data-table_name="results"]/tbody/tr[{row}]/td[4]')
            if c.text in (df2["competition"].tolist()):
                while curr_weight == weight_col.text:
                    curr_date = date_col.text
                    curr_comp = c.text
                    break
                while curr_weight != weight_col.text:
                    if curr_comp:
                        results.append([i, curr_weight, curr_date, curr_comp])
                    curr_weight = weight_col.text
                    curr_date = date_col.text
                    curr_comp = c.text
                    results.append([i, weight_col.text, date_col.text, c.text])
            row += 1
        results.append([i, curr_weight, curr_date, curr_comp])
        results.reverse()
        for r in results:
            del r[3]

        pl_id = []
        kgs = []
        oddstart_evenstop = []

        for x in results:
            pl_id.append(x[0])
            kgs.append(x[1])
            oddstart_evenstop.append(x[2])

        final_pl_id = (pl_id[::2])
        final_kgs = (kgs[::2])
        final_start = (oddstart_evenstop[::2])
        final_stop = (oddstart_evenstop[1::2])
        final_stop[-1] = None

        player_id.extend(final_pl_id)
        weight_cat.extend(final_kgs)
        start_time.extend(final_start)
        end_time.extend(final_stop)

        driver.navigate().refresh()  # added this today and will run to see if it resolves issue of chrome crashing


    # print(player_id)
    # print(weight_cat)
    # print(start_time)
    # print(end_time)

    weights: DataFrame = pd.DataFrame(np.column_stack([player_id, weight_cat, start_time, end_time]),
                                       columns=['player_id', 'weight_cat', 'start_time', 'end_time'])

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    weights.set_index('player_id', inplace=True)

    # weights.to_csv('weights.csv')


# get_weights()


def get_matches():
    df = tournaments

    comp_list = []
    id_list = []
    win_list = []
    round_list = []

    for i in df.index:
        driver.get(f'https://judobase.ijf.org/#/competition/profile/{i}/contests/0')
        WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="c1"]')))
        id_cols = driver.find_elements(By.XPATH, '//*[@id="tile_view"]/div[2]/div/div/div/div/div/div/div/ul/li/a')

        for c in id_cols:
            links = c.get_attribute('href')
            temp = re.findall(r'\d+', links)
            res = ''.join(map(str, temp))
            if res:
                id_list.append(res)

        winners = (driver.find_elements(By.XPATH, '// *[ @ id = "tile_view"] / div[2] / div / div / div / div / div'))
        for w in winners:
            if w.get_attribute('class') == 'js-contest contest winner-a':
                win_list.append('Player 1 Wins')
            elif w.get_attribute('class') == 'js-contest contest winner-b':
                win_list.append('Player 2 Wins')
            elif w.get_attribute('class') == 'js-contest contest':
                win_list.append('No Winner')

        rounds = driver.find_elements(By.XPATH, '//div[@class="round"]')
        for r in rounds:
            round_list.append(r.text)
            comp_list.append(i)



    matches: DataFrame = pd.DataFrame(np.column_stack([comp_list, id_list[::2], id_list[1::2], round_list, win_list]),
                                       columns=['comp_id', 'player_1_id', 'player_2_id', 'round', 'result'])

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    matches.set_index('comp_id', inplace=True)

    # matches.to_csv('matches.csv')

# get_matches()
