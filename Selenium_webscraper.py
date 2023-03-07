import time
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
import csv

# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

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
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//div[@class="well"]')))
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
                                columns=['comp_id', 'comp_name', 'host_country', 'start_date', 'end_date'])
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    competitions.set_index('comp_id', inplace=True)

    discard = ["Kata"]
    competitions = competitions[~competitions.comp_name.str.contains('|'.join(discard))]
    competitions['start_date'] = pd.to_datetime(competitions['start_date'], format='%Y-%m-%d')
    competitions = competitions.loc[(competitions['start_date'] > '2016-09-22')]

    #  to save as CSV file
    # competitions.to_csv('competitions.csv')

    return competitions


# get_competitions()

# tournaments = get_competitions()


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
            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//div[@class="js-categories"]')))
            players_id = (driver.find_elements(By.XPATH, '//tr[@data-id_person]'))
            names = (driver.find_elements(By.XPATH, '//td[@data-name="full_name"]'))
            countries = (driver.find_elements(By.XPATH, '//span[@title]'))
            for p_id in players_id:
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

    players: DataFrame = pd.DataFrame(np.column_stack([player_ids, player_names, player_countries, player_sex]),
                                      columns=['player_id', 'player_name', 'nationality', 'sex'])

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    players.set_index('player_id', inplace=True)

    players = players.groupby(players.index).first()

    # players.to_csv('players.csv')

    return players


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
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, '//td[@class=" sorting_1"]')))

        comp_col = driver.find_elements(By.XPATH, '//*[@data-table_name="results"]/tbody/tr/td[3]')

        results = []
        row = 1
        curr_weight = ''
        curr_date = ''
        curr_comp = ''

        for c in comp_col:
            date_col = driver.find_element(By.XPATH, f'//*[@data-table_name="results"]/tbody/tr[{row}]/td[2]')
            weight_col = driver.find_element(By.XPATH, f'//*[@data-table_name="results"]/tbody/tr[{row}]/td[4]')
            if c.text in (df2["comp_name"].tolist()):
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
                                      columns=['player_id', 'weight', 'start_date', 'end_date'])

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
    match_id_list = []
    pl_id_list = []
    win_list = []
    round_list = []

    for i in df.index:
        weight_page = 1
        while weight_page < 15:
            driver.get(f'https://judobase.ijf.org/#/competition/profile/{i}/contests/{weight_page}')
            driver.refresh()

            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//a[@href="#table_view"]')))
            table_view = driver.find_element(By.XPATH, '//a[@href="#table_view"]')
            driver.execute_script("arguments[0].click();", table_view)

            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, '//span[@class="glyphicon glyphicon-play"]')))

            id_cols = driver.find_elements(By.XPATH, '//*[@id="tile_view"]/div[2]/div/div/div/div/div/div/div/ul/li/a')
            curr_pl_ids = []
            for c in id_cols:
                links = c.get_attribute('href')
                temp = re.findall(r'\d+', links)
                res = ''.join(map(str, temp))
                if res:
                    pl_id_list.append(res)
                    curr_pl_ids.append(res)

            winner_rows = (driver.find_elements(By.XPATH, '/ html / body / div[1] / div[2] / div / div[2] / div / div / div / div[1] / div / div / table / tbody / tr / \
              td[5]'))

            loop_pairs = 0
            hand_row = 1
            for r in range(len(winner_rows)):
                try:
                    hand_point = driver.find_element(By.XPATH,
                                                     f"//html/body/div[1]/div[2]/div/div[2]/div/div/div/div[1]/div/div/table/tbody/tr[{hand_row}]/td[5]/i")
                    if hand_point.get_attribute('class') == 'glyphicon glyphicon-hand-left':
                        win_list.append(curr_pl_ids[loop_pairs])
                        loop_pairs += 2
                        hand_row += 1
                    elif hand_point.get_attribute('class') == 'glyphicon glyphicon-hand-right':
                        win_list.append(curr_pl_ids[loop_pairs + 1])
                        loop_pairs += 2
                        hand_row += 1
                except NoSuchElementException:
                    win_list.append(None)
                    loop_pairs += 2
                    hand_row += 1

            rounds = driver.find_elements(By.XPATH, '//span[@data-sstr]')
            for r in rounds:
                round_list.append(r.text)
                comp_list.append(i)

            match_ids = driver.find_elements(By.XPATH, '//td[@class=" sorting_1"]')
            for m in match_ids:
                if weight_page == 1:
                    match_id_list.append(f'0060_{int(m.text):04d}')
                if weight_page == 2:
                    match_id_list.append(f'0066_{int(m.text):04d}')
                if weight_page == 3:
                    match_id_list.append(f'0073_{int(m.text):04d}')
                if weight_page == 4:
                    match_id_list.append(f'0081_{int(m.text):04d}')
                if weight_page == 5:
                    match_id_list.append(f'0090_{int(m.text):04d}')
                if weight_page == 6:
                    match_id_list.append(f'0100_{int(m.text):04d}')
                if weight_page == 7:
                    match_id_list.append(f'p100_{int(m.text):04d}')
                if weight_page == 8:
                    match_id_list.append(f'0048_{int(m.text):04d}')
                if weight_page == 9:
                    match_id_list.append(f'0052_{int(m.text):04d}')
                if weight_page == 10:
                    match_id_list.append(f'0057_{int(m.text):04d}')
                if weight_page == 11:
                    match_id_list.append(f'0063_{int(m.text):04d}')
                if weight_page == 12:
                    match_id_list.append(f'0070_{int(m.text):04d}')
                if weight_page == 13:
                    match_id_list.append(f'0078_{int(m.text):04d}')
                if weight_page == 14:
                    match_id_list.append(f'0p78_{int(m.text):04d}')

            weight_page += 1

    matches: DataFrame = pd.DataFrame(
        np.column_stack([comp_list, match_id_list, pl_id_list[::2], pl_id_list[1::2], round_list, win_list]),
        columns=['comp_id', 'match_id', 'player1_id', 'player2_id', 'round', 'winner_id'])

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    matches.set_index('match_id', inplace=True)

    # matches.to_csv('matches.csv')


# get_matches()


def get_match_details():
    comp_csv_data = pd.read_csv('competitions.csv')
    comp_col = pd.DataFrame(comp_csv_data)
    comp_id_list = comp_col['comp_id'].values.tolist()

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    comp_url_list = []
    for i in comp_id_list:
        driver.get(f'https://judobase.ijf.org/#/competition/profile/{i}/statistics')
        time.sleep(2)
        comp_url = driver.find_element(By.XPATH, "//div[@class='menu_views_bg_01']").value_of_css_property(
            'background-image')
        comp_url_list.append([i, (re.split('banners/|.jpg', comp_url)[1])])
    driver.quit()

    match_csv_data = pd.read_csv('matches.csv')
    match_comp_cols = pd.DataFrame(match_csv_data, columns=['comp_id', 'match_id', 'player1_id', 'player2_id'])
    match_id_list = match_comp_cols.values.tolist()

    male = ['0060', '0066', '0073', '0081', '0090', '0100', 'p100']
    female = ['0048', '0052', '0057', '0063', '0070', '0078', '0p78']
    full_list = []

    for c in comp_url_list:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        for m in match_id_list:
            if c[0] == m[0] and m[1].startswith(tuple(male)):
                driver.get(f'https://judobase.ijf.org/#/competition/contest/{c[1]}_m_{m[1]}')
                row = 1
                try:
                    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, '//tr[@class="js-event"]')))
                    scores = driver.find_elements(By.XPATH, '//tr[@class="js-event"]')
                except UnexpectedAlertPresentException:
                    continue
                except TimeoutException:
                    print(c[0], c[1], m[0], m[1])
                    continue

                for s in range(len(scores)):
                    WebDriverWait(driver, 30).until(
                        EC.visibility_of_element_located((By.XPATH, '//*[@id="playerIframe"]')))
                    match_url = driver.find_element(By.XPATH, '//*[@id="playerIframe"]')
                    match_attr = match_url.get_attribute("src")
                    match_num = re.split('_\D_|\?', match_attr)[1]
                    p1_score = driver.find_element(By.XPATH,
                                                   f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[1]')
                    p2_score = driver.find_element(By.XPATH,
                                                   f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[3]')

                    if p2_score.text == '':
                        timestamp = driver.find_element(By.XPATH,
                                                        f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[2]')
                        score = p1_score.text.replace('\n', ': ')
                        full_list.append([c[0], match_num, m[2], score, timestamp.text])
                        row += 1

                    elif p1_score.text == '':
                        timestamp = driver.find_element(By.XPATH,
                                                        f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[2]')
                        score = p2_score.text.replace('\n', ': ')
                        full_list.append([c[0], match_num, m[3], score, timestamp.text])
                        row += 1

                    else:
                        timestamp = driver.find_element(By.XPATH,
                                                        f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[2]')
                        score_1 = p1_score.text.replace('\n', ': ')
                        score_2 = p2_score.text.replace('\n', ': ')
                        full_list.append([c[0], match_num, m[2], score_1, timestamp.text])
                        full_list.append([c[0], match_num, m[3], score_2, timestamp.text])
                        row += 1

            elif c[0] == m[0] and m[1].startswith(tuple(female)):
                driver.get(f'https://judobase.ijf.org/#/competition/contest/{c[1]}_w_{m[1]}')
                row = 1
                try:
                    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, '//tr[@class="js-event"]')))
                    scores = driver.find_elements(By.XPATH, '//tr[@class="js-event"]')
                except UnexpectedAlertPresentException:
                    continue
                except TimeoutException:
                    print(c[0], c[1], m[0], m[1])
                    continue

                for s in range(len(scores)):
                    WebDriverWait(driver, 30).until(
                        EC.visibility_of_element_located((By.XPATH, '//*[@id="playerIframe"]')))
                    match_url = driver.find_element(By.XPATH, '//*[@id="playerIframe"]')
                    match_attr = match_url.get_attribute("src")
                    match_num = re.split('_\D_|\?', match_attr)[1]
                    p1_score = driver.find_element(By.XPATH,
                                                   f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[1]')
                    p2_score = driver.find_element(By.XPATH,
                                                   f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[3]')

                    if p2_score.text == '':
                        timestamp = driver.find_element(By.XPATH,
                                                        f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[2]')
                        score = p1_score.text.replace('\n', ': ')
                        full_list.append([c[0], match_num, m[2], score, timestamp.text])
                        row += 1

                    elif p1_score.text == '':
                        timestamp = driver.find_element(By.XPATH,
                                                        f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[2]')
                        score = p2_score.text.replace('\n', ': ')
                        full_list.append([c[0], match_num, m[3], score, timestamp.text])
                        row += 1

                    else:
                        timestamp = driver.find_element(By.XPATH,
                                                        f'/html/body/div[1]/div[2]/div/div[2]/div/div/div/div[6]/table/tbody/tr[{row}]/td[2]')
                        score_1 = p1_score.text.replace('\n', ': ')
                        score_2 = p2_score.text.replace('\n', ': ')
                        full_list.append([c[0], match_num, m[2], score_1, timestamp.text])
                        full_list.append([c[0], match_num, m[3], score_2, timestamp.text])
                        row += 1

        driver.quit()

    comp_id = [sublist[0] for sublist in full_list]
    match_id = [sublist[1] for sublist in full_list]
    player_id = [sublist[2] for sublist in full_list]
    event = [sublist[3] for sublist in full_list]
    event_time = [sublist[4] for sublist in full_list]

    match_details: DataFrame = pd.DataFrame(np.column_stack([comp_id, match_id, player_id, event, event_time]),
                                            columns=['comp_id', 'match_id', 'player_id', 'event', 'time'])

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    match_details.set_index('match_id', inplace=True)

    # match_details.to_csv('match_details.csv')


# get_match_details()
