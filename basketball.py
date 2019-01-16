#!/#!/usr/bin/env python3

import requests
import pandas as pd

from bs4 import BeautifulSoup


def get_tables(url):

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    # tables are hidden behind html comments. This parses that
    macaroni = soup.prettify().split('<!--')
    macaroni = [mac.strip('-->') for mac in macaroni]

    tables = []

    for roi in macaroni:
        table = BeautifulSoup(roi, 'lxml').find_all('table')
        if table != []:
            tables.append(table[0])

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


# commenting out the below because I don't need every single table
# I'll come to tables as I need them.
# For now, I will focus on Per 36 Min table

# def clean_tables(dfs):  # I'll run a for loop for each df in dfs
#     '''
#     Takes list of pandas dataframes for an NBA team in 1999 and cleans each
#     DataFrame
#     '''
#     clean_dfs = []

#     # clean df 0
#     df0 = dfs[0]
#     df0 = df0.apply(str.strip)  # strip white space from number
#     clean_dfs.append(df0)

#     # df 1 is already clean
#     df1 = dfs[1]
#     df1.columns = ['Name', 'Title']
#     clean_dfs.append(df1)

#     # clean df 2
#     df2 = dfs[2]
#     df2.columns = df2.iloc[0, :]
#     df2.drop(0, inplace=True)
#     df2.reset_index(inplace=True, drop=True)
#     clean_dfs.append(df2)

#     # clean df 3
#     df3 = dfs[3]
#     [3].drop(0, inplace=True)
#     cols = df3.iloc[0, :]
#     df3.columns = cols
#     df3.drop(1, inplace=True)
#     df3.reset_index(inplace=True)
#     clean_dfs.append(df3)

#     # clean df 4




if __name__ == '__main__':

    # testing on just one team, one season
    URL = 'https://www.basketball-reference.com/teams/SAS/1999.html'
    dfs = get_tables(URL)

    print(dfs[9])
