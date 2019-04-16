#!/usr/bin/env python3

import requests
import pickle
import time
import pandas as pd
import numpy as np


from bs4 import BeautifulSoup


def get_tables(url):
    """Return table from basketball-reference.com"""

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    # tables are hidden behind html comments. This parses that
    macaroni = soup.prettify().split('<!--')
    macaroni = [mac.strip('-->') for mac in macaroni]

    tables = []

    for roi in macaroni:  # roi = region of interest

        table = BeautifulSoup(roi, 'lxml').find_all('table')

        if table != []:  # make sure that the roi contained a table
            tables.append(table[0])

    dfs = []

    # convert table from html to list of lists to pd.DataFrame
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

def get_teams_for_year(year=1999):
    """Returns list of active team abbreviations in NBA for given year"""

    #  WARNING: have not tested on years other than 1999

    url = 'https://www.basketball-reference.com/leagues/NBA_{}.html'.format(year)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')

    # this gets a list of the all teams in the nba
    trs = soup.find_all('tr')

    team_links = []
    teams = []

    for tr in trs:
        if tr.a:
            link = tr.a['href'].strip('/teams/').strip('/')
            team_links.append(link)
            teams.append(link.strip('/{}.html'.format(year)))

    return teams, team_links


def get_database(year=1999):

    teams, team_links = get_teams_for_year(year=year)

    urls = ['https://www.basketball-reference.com/teams/{}'.format(link) for link in team_links]

    database = {}
    for url, team in zip(urls, teams):
        database[team] = get_tables(url)

    return database


def database_to_stats_and_salaries(pos=6, year=1999, database=None):
    """
    Take database and returns specific stats table and salary tables
    for pos (position) argument:
        6 --> per 36 minute table
        8 --> advanced stats table
    """

    if database == None: # want to allow a database to be passed
        database = get_database(year)

    dfs_per_36 = {}

    for team, dfs in database.items():
        clean_df = dfs[pos].copy()  # the 6th table is always the per36 stats
        clean_df.iloc[0,1] = 'Name'
        clean_df.columns = clean_df.iloc[0,:]
        clean_df.drop(0, inplace=True)
        clean_df.reset_index(inplace=True, drop=True)
        dfs_per_36[team] = clean_df


    salaries = {}

    for team, dfs in database.items():
        new_df = dfs[-1].copy()  # the salary table is the last on the page
        new_df.iloc[0,1] = 'Name'  # fill in blank column name
        new_df.columns = new_df.iloc[0, :]
        new_df.drop(0, inplace=True)
        new_df.reset_index(inplace=True, drop=True)

        # money to float
        new_df['Salary'].replace('\D', '', regex=True, inplace=True)
        new_df['Salary'] = pd.to_numeric(new_df['Salary'])

        # add to dicitonary
        salaries[team] = new_df

    return dfs_per_36, salaries


def stats_salary_join(year=None, dfs=None, targets=None):
    "merges per36min table and salary for all teams in a year and returns resulting DataFrame"

    if ((dfs == None) | (targets == None) | (year == None)):
        dfs, targets = database_to_36min_and_salaries(year=1999)
        year = 1999

    data = []

    for team in dfs.keys():
        df = dfs[team]
        sal = targets[team]
        sal.drop('Rk', axis=1, inplace=True)
        try:
            new_df = pd.concat([df.set_index('Name'), sal.set_index('Name')], axis=1, join='inner')
        except ValueError:
            print('Failed to concat {}'.format(team))
            continue
        new_df['Team'] = team
        new_df['Year'] = year
        new_df.reset_index(inplace=True)
        new_df.set_index(['Name', 'Team', 'Year'], inplace=True)
        data.append(new_df)

    final_df = pd.concat(data)
    final_df = final_df.apply(pd.to_numeric) # the per36 tables weren't numeric yet

    return final_df

# this next one didn't really work
def get_multiple_years(start=2008, end=2018):

    dfs = []
    for year in range(start, end + 1):

        # this try-except is untested. It would take 10 min so I don't want to right now
        try:
            df = stats_salary_join(year)
        except ValueError:
            continue
        dfs.append(df)

    return pd.concat(dfs)


def clean_columns(df):
    """Cleans some rows and adds a feature. The mapper is to make those features available
    for stats models."""

    mapper = {'2P':'TwoPoint',
              '2PA':'TwoPointAttempt',
              '2P%':'TwoPointPercent',
              'FG%': 'FieldGoalPercent',
              'FT%':'FreeThrowPercent',
              '3P%': 'ThreePointPercent'
         }

    df.rename(columns=mapper, inplace=True)

    preliminary_columns = ['DRB', 'TwoPoint', 'PTS', 'FG', 'BLK', 'FT',
                           'TwoPointAttempt', 'Age', 'PF', 'Salary']

    to_remove = ['Salary', 'FreeThrowPercent', 'ThreePointPercent',
                 'TwoPointPercent', 'FieldGoalPercent']

    columns = list(df.columns)
    for column in to_remove:
        columns.remove(column)

    # let's drop players with low minutes played per game, say less than 10
    df['MPperG'] = df['MP']/df['G']

    mask = (df['MPperG'] > 10)
    df_over_10 = df[mask]

    return df_over_10


def prepare_dataframe(df):

    mapper = {
        '2P': 'TwoPoint',
        '2PA': 'TwoPointAttempt',
        '2P%': 'TwoPointPercent',
        'FG%': 'FieldGoalPercent',
        'FT%': 'FreeThrowPercent',
        '3P%': 'ThreePointPercent'
    }

    df.rename(columns=mapper, inplace=True)

    to_remove = ['Salary', 'FreeThrowPercent', 'ThreePointPercent',
                 'TwoPointPercent', 'FieldGoalPercent']

    columns = list(df.columns)
    for column in to_remove:
        columns.remove(column)

    # let's drop players with low minutes played per game, say less than 10
    df['MPperG'] = df['MP'] / df['G']

    # We want over 10 minutes played per game and nonzero salary
    mask = ((df['MPperG'] > 10) & (df['Salary'] > 0))
    df = df[mask]

    X = df[columns].values
    y = df['Salary'].values
    y = np.log(y)

    return X, y, df


if __name__ == '__main__':

    # testing on just one team, one season
    df = stats_salary_join()

    with open('final_df.pickle', 'wb') as f:
        pickle.dump(df, f)

    print(df.sample(5))
