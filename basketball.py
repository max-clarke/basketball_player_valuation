#!/#!/usr/bin/env python3

import requests
import pandas as pd

from bs4 import BeautifulSoup


def get_tables(url):

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    # tables are hiddne behond html comments. This parses that
    macaroni = soup.prettify().split('<!--')
    macaroni = [mac.strip('-->') for mac in macaroni]

    tables = []

    for nood in macaroni:
        udon = BeautifulSoup(nood, 'lxml').find_all('table')
        if udon != []:
            tables.append(udon[0])

    dfs = []

    for table in tables:
        rows = table.find_all('tr')
        data = []

        for row in rows:
            row_data = []

            for entry in row.find_all('th'):  # headers
                row_data.append(entry.text)

            for entry in row.find_all('td'):  # datums
                row_data.append(entry.text)

            data.append(row_data)

        dfs.append(pd.DataFrame(data))

    return dfs

if __name__ == '__main__':

    # testing on just one team, one season
    URL = 'https://www.basketball-reference.com/teams/SAS/2006.html'
    dfs = get_tables(URL)

    print(dfs[9])
