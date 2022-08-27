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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//div[@class="js-categories"]')))
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

    athletes.to_csv('athletes.csv')

    return athletes


# get_players()

# athletes = get_players()


def get_weights():
    player_id = []
    weight_cat = []
    start_time = []
    end_time = []
    df1 = athletes
    for i in df1.index:
        df2 = tournaments
        driver.get(f'https://judobase.ijf.org/#/competitor/profile/{i}/results')
        driver.refresh()
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

    weights: DataFrame = pd.DataFrame(np.column_stack([player_id, weight_cat, start_time, end_time]),
                                      columns=['player_id', 'weight_cat', 'start_time', 'end_time'])

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    weights.set_index('player_id', inplace=True)

    weights.to_csv('weights.csv')


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

    matches.to_csv('matches.csv')


# get_matches()


def get_match_details():
    df = tournaments
    full_list = []

    for i in df.index:
        driver.get(f'https://judobase.ijf.org/#/competition/profile/{i}/contests/0')

        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//a[@href="#table_view"]')))
        table_view = driver.find_element(By.XPATH, '//a[@href="#table_view"]')
        driver.execute_script("arguments[0].click();", table_view)

        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//span[@class="glyphicon glyphicon-play"]')))
        matches = driver.find_elements(By.XPATH, '//span[@class="glyphicon glyphicon-play"]')
        match_row = 1
        for m in range(len(matches)):
            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//span[@class="glyphicon glyphicon-play"]')))
            while True:
                try:
                    play_button = driver.find_element(By.XPATH, f"//tbody/tr[{match_row}]/td[14]/div/span")
                    driver.execute_script("arguments[0].click();", play_button)
                    driver.refresh()
                except NoSuchElementException:
                    match_row += 1
                    continue
                break

            try:
                WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="col-xs-6"]')))

            except TimeoutException:
                driver.refresh()
                WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="col-xs-6"]')))

            player_1 = driver.find_element(By.XPATH, '//div[@class="col-xs-6 text-right"]').text
            player_2 = driver.find_element(By.XPATH, '//div[@class="col-xs-6"]').text
            p1 = player_1[:-4]
            p2 = player_2[:-4]

            scores = driver.find_elements(By.XPATH, '//tr[@class="js-event"]')
            row = 1
            for s in range(len(scores)):
                WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="playerIframe"]')))
                match_url = driver.find_element(By.XPATH, '//*[@id="playerIframe"]')
                match_attr = match_url.get_attribute("src")
                match_num = re.split('_\D_|\?', match_attr)[1]
                p1_score = driver.find_element(By.XPATH, f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[1]')
                p2_score = driver.find_element(By.XPATH, f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[3]')

                if p2_score.text == '':
                    timestamp = driver.find_element(By.XPATH, f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[2]')
                    score = p1_score.text.replace('\n', ': ')
                    full_list.append([i, match_num, p1, score, timestamp.text])
                    row += 1

                elif p1_score.text == '':
                    timestamp = driver.find_element(By.XPATH, f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[2]')
                    score = p2_score.text.replace('\n', ': ')
                    full_list.append([i, match_num, p2, score, timestamp.text])
                    row += 1

                else:
                    timestamp = driver.find_element(By.XPATH, f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[2]')
                    score_1 = p1_score.text.replace('\n', ': ')
                    score_2 = p2_score.text.replace('\n', ': ')
                    full_list.append([i, match_num, p1, score_1, timestamp.text])
                    full_list.append([i, match_num, p2, score_2, timestamp.text])
                    row += 1

            driver.back()
            match_row += 1
            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//a[@href="#table_view"]')))
            table_view = driver.find_element(By.XPATH, '//a[@href="#table_view"]')
            driver.execute_script("arguments[0].click();", table_view)

            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//span[@class="glyphicon glyphicon-play"]')))

    comp_id = [sublist[0] for sublist in full_list]
    match_id = [sublist[1] for sublist in full_list]
    player = [sublist[2] for sublist in full_list]
    event = [sublist[3] for sublist in full_list]
    event_time = [sublist[4] for sublist in full_list]

    match_details: DataFrame = pd.DataFrame(np.column_stack([comp_id, match_id, player, event, event_time]),
                                      columns=['comp_id', 'match_id', 'player', 'event', 'time'])

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    match_details.set_index('match_id', inplace=True)

    match_details.to_csv('match_details.csv')


# get_match_details()
