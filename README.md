# Basketball Player Valuation

## Webscraping/Regression Project:

### Goals for project

In this project, I wanted to apply regression techniques to see how player stats relate to player salary in the same year. Assuming that I have a good model for predicting salary, I could then look at the difference between predicted and actual salary as a measure of whether a given player was over or undervalued. 

### Process and Methods

I used Beautiful Soup and requests to perform web scraping on <https://www.basketball-reference.com/>, a comprehensive source of basketball statistics, containing everything from basic stats such as number of personal fouls and points scored, to advanced statistics such as BPM (Box Plus/Minus) and PER (Player Efficiency Rating).

The data that I collected spanned a decade, from 2008 to 2018. Since salaries are constantly inflating, I decided to normalize each players salary to be a percentage of their salary cap.

### Files

In `basketball.py` are a collection of functions for retrieving, organizing, and cleaning data. 

In `analysis.ipynb` is some work I did training models and predicting salaries. I determined the most undervalued and most overvalued for each year in my dataset.

In `data/` are several pickled files containing pandas data frames holding the data from basketball-reference. 