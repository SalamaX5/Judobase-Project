import re
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

start_div = 1  # start at -60kg

end_comp = 2239  # last comp before Tokyo Olympics
end_div = 14  # end at +78 kg

relevant_comps = ["Grand Prix", "Grand Slam", "Masters", "World Senior Championship", "World Championships Senior",
                  "World Judo Championships Seniors"]


def get_competitions():
    start_comp = 1341  # first comp after 2016 Rio Olympics
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

    print(competitions)

    #  to save as CSV file
    #  competitions.to_csv('competitions.csv')


get_competitions()
