#!/#!/usr/bin/env python3

import requests
import pickle
import time
import pandas as pd


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

    teams, team_links = get_teams_for_year(year)

    urls = ['https://www.basketball-reference.com/teams/{}'.format(link) for link in team_links]

    database = {}

    for url, team in zip(urls, teams):
    
        database[team] = get_tables(url)

    return database

def database_to_36min_and_salaries():
    
    database = get_database()

    dfs_per_36 = {}

    for team, dfs in database.items():
        clean_df = dfs[6].copy()  # the 6th table is always the per36 stats
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


def stats_salary_join():

    dfs, targets = database_to_36min_and_salaries()

    data = []

    for team in dfs.keys():
        df = dfs[team]
        sal = targets[team]
        sal.drop('Rk', axis=1, inplace=True)
        new_df = pd.concat([df.set_index('Name'), sal.set_index('Name')], axis=1, join='inner')
        data.append(new_df)

    final_df = pd.concat(data)
    final_df = final_df.apply(pd.to_numeric) # the per36 tables weren't numeric yet

    return final_df






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
    df = stats_salary_join()
    
    with open('final_df.pickle', 'wb') as f:
        pickle.dump(df, f)

    print(df.sample(5))