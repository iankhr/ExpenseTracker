# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 20:33:25 2019

@author: Ian
"""

import pandas as pd
import os
import numpy as np
import localdb as db
import matplotlib.pyplot as plt

# set current dir
CWD = os.getcwd()
IMPORT = '\\Import'

def readexcel(filename):
    # understand which data are you dealing with
    if 'SEB' in filename:
        # read data in pandas dataframe
        data = pd.read_excel(CWD+IMPORT+'\\'+filename)
        # account identifier
        account = filename.split('_')[-1].split('.')[0]
        # it's SEB excel sheet
        cash = data.iloc[0,2]
        # separate transactions
        transactions = data.iloc[4:,:].reset_index(drop=True)
        transactions.columns = data.iloc[3,:].tolist()
        # SEB usually puts payment in message
        transactions['transdate'] = ['20'+transactions.iloc[i, 3].split('/')[-1] \
                     if '/' in transactions.iloc[i, 3]\
                     else transactions.iloc[i, 0]
                     for i in transactions.index]
        # convert to date
        transactions['transdate'] = pd.to_datetime(transactions['transdate'])
        # cut data before 2019
        transactions =transactions[transactions['transdate']>pd.to_datetime('2019-01-01')]
        # rename columns
        transactions.columns = ['date1','date2','verification', 'msg', 'amount',\
                                'saldo','date']
    elif 'ICA' in filename:
        # read data in pandas dataframe
        data = pd.read_csv(CWD+IMPORT+'\\'+filename, sep=';')
        # converting numerals
        data.iloc[:,5] = data.iloc[:,5].apply(lambda x:\
                 float(x[:-3].replace(',','.').replace(' ','')))
        data.iloc[:,4] = data.iloc[:,4].apply(lambda x:\
                 float(x[:-3].replace(',','.').replace(' ','')))
        # account identifier
        account = filename.split('_')[-1].split('.')[0]
        cash = data.iloc[0,5]
        transactions = data[['Datum', 'Text','Belopp','Saldo']]
        transactions.columns = ['date','msg','amount','saldo']
        transactions['date'] = pd.to_datetime(transactions['date'])
        
    # remove file from the import folder
    os.remove(CWD+IMPORT+'\\'+filename)
    return [account, cash, transactions]

def guesscategory(text):
    phrase = text.split('/')[0]
    keywords = db.readData('keywords')
    categorylist = db.readData('categories')
    sresult = keywords['keyword'].str.contains(phrase)
    if (len(sresult) == 0) | (~np.any(sresult)):
        # learn what the category is
        print(categorylist.values)
        categoryid = input('Define category for {}: '.format(phrase))
        try:
            categoryid = int(categoryid)
        except:
            print(categoryid)
            raise ValueError('Category must be integer')
        data = pd.DataFrame([phrase, categoryid], index = ['keyword', 'categoryid']).T
        db.insertData(data,'keywords')
    else:
        # get index
        categoryid = keywords.loc[sresult, 'categoryid'].values
        if len(categoryid)>1:
            print(categoryid)
            categoryid = input('Define category for {}: '.format(phrase))
        try:
            categoryid = int(categoryid)
        except:
            print(categoryid)
            raise ValueError('Category must be integer')
    
    return categoryid

def dataframe_difference(df1, df2, which=None):
    """Find rows which are different between two DataFrames.
    
    which takes 'left_only', 'right_only' or 'both'
    By Todd Birchard from https://hackingandslacking.com/comparing-rows-between-two-pandas-dataframes-c3b174ff560e
    """
    comparison_df = df1.merge(df2,
                              indicator=True,
                              how='outer')
    if which is None:
        diff_df = comparison_df[comparison_df['_merge'] != 'both']
    else:
        diff_df = comparison_df[comparison_df['_merge'] == which]
    #diff_df.to_csv('data/diff.csv')
    return diff_df

def update():
    # scan for any files
    filelist = os.listdir(CWD+IMPORT)
    if len(filelist)>0:
        # there some files available
        filedata = [readexcel(file) for file in filelist]
        for i in range(len(filedata)):
            # identify groups based on the transaction types
            filedata[i][2]['category'] = [guesscategory(filedata[i][2].loc[j, 'msg'])\
                                 for j in filedata[i][2].index]
            # write down into database
            filedata[i][2]['account'] = filedata[i][0]
            temp = filedata[i][2][['date', 'account', 'amount', 'msg', 'category']]
            temp['amount'] = temp['amount'].astype(float)
            # read latest 
            loggedtrans = db.readData('transactions',\
                                      where = "account = '{}'".format(filedata[i][0]))
            loggedtrans['date'] = pd.to_datetime(loggedtrans['date'])
            # get rows that are new
            temp = dataframe_difference(temp, loggedtrans.drop('rowid', axis=1),\
                                        which='left_only').drop('_merge', axis=1)
            if not temp.empty:
                # write latest transactions to database
                db.insertData(temp,'transactions')
            
            # update available funds
            tempaccount = pd.DataFrame([filedata[i][0], pd.to_datetime('today'),\
                                        filedata[i][1]], index = ['account', 'date','balance']).T
            # check whether it already exists
            loggedaccount = db.readData('accounts',\
                                      where = "account = '{}'".format(filedata[i][0]))
            if loggedaccount.empty:
                db.insertData(tempaccount,'accounts')
            else:
                # select rowid
                db.alterData(tempaccount, 'accounts',\
                             where = 'rowid = {}'.format(\
                                    loggedaccount.loc[:,'rowid'].values[0]))

def getCurrentMonthExpenses(month = None, account = None):
    """
    The functions makes query to database and returns the list of expenses. If 
    nothing provided that all of the expenses are returned
    
    INPUT:
        month - string with mm/yyyy format(!); where mm and yyyy are numerical
        account - string with name of account
    OUTPUT:
        expenses - pandas DataFrame with expenses with columns rowid, date,
                   account, amount, msg and category
    """
    whereQuery = ''
    if month is not None:
        whereQuery  = whereQuery + 'MONTH(date) = {}'.format(\
                                         int(month.split('/')[0]))\
                                 + ' AND YEAR(date) = {}'.format(\
                                        int(month.split('/')[1]))
    if (month is not None) & (account is not None):
        whereQuery = whereQuery +' AND '
        
    if account is not None:
        whereQuery = whereQuery + "account = '{}'".format(account)
    
    if whereQuery == '':
        whereQuery = None
    # get transactions
    expenses = db.readData('transactions', where = whereQuery)
    return expenses
    
def aggregateExpenses(transactionList):
    """
    Takes into a list of transactions and returns the summarized statistics
    
    INPUT
        transactionList - pandas DataFrame with columns: date, account, amount,
                          masg and category
    OUTPUT
        totexp - total expenses per day
        totGroupExpenses - detailed aggregation of expenses per category
        totGroupIncome - detailed aggregation of income per category
    """
    # group by date and date
    expgroup = transactionList.groupby('date')
    # get total expenses per day
    totexp = -expgroup.sum()
    # group by category
    catgroup = transactionList.groupby('category')
    # get total expenses per category
    totgroup = -catgroup.sum()
    totgroup = totgroup[totgroup['amount'] != 0]
    # match with categories
    categories = db.readData('categories')
    totgroup = totgroup.join(categories.set_index('categoryid'))
    # select expenses only
    totGroupExpenses = totgroup[totgroup['amount']>0]
    totGroupIncome = -totgroup[totgroup['amount']<0]
    return totexp['amount'], totGroupExpenses[['amount', 'categoryname',\
                 'monthlyLimit']],\
           totGroupIncome[['amount', 'categoryname', 'monthlyLimit']]


def setMonthlyLimit(categoryid, limit):
    """
    Function sets monthly expense limit, which is then comapred with current
    expenses in the program.
    INPUT
        categoryid - integer, which is categories for category id
        limit - float in swedish krowns(or basis currency)
    OUTPUT
        -
    """  
    if type(categoryid) is not list:
        # select rowid 
        data = pd.DataFrame([limit,], index = ['monthlyLimit',]).T
        db.alterData(data, 'categories',\
                 where = 'categoryid = {}'.format(categoryid))
    else:
        for i in range(len(categoryid)):
            data = pd.DataFrame([limit[i],], index = ['monthlyLimit',]).T
            db.alterData(data, 'categories',\
                 where = 'categoryid = {}'.format(categoryid[i]))
    
if __name__ == '__main__':
    # update the database
    update()
    # load transactions
    transactions = getCurrentMonthExpenses('11/2019')
    # group data
    NetExpenses, totalExpenses, totalIncome = aggregateExpenses(transactions)
    # plot all of the expenses 
    if NetExpenses.empty:
        print('No expenses to plot!')
    else:
        NetExpenses.plot.bar(title = 'Total Net Expenses')
        plt.show()
        NetExpenses.cumsum().plot.bar(title = 'Total Cumulative Expenses')
        plt.show()
    if totalExpenses.empty:
        print('No expenses to plot!')
    else:
        totalExpenses.set_index('categoryname')['amount'].sort_values(\
                               ascending=False).plot.bar(\
                     title = 'Total Expenses by Group')
        plt.show()
    if totalIncome.empty:
        print('No Income to plot!')
    else:
        totalIncome['amount'].set_index('categoryname').plot.bar(\
                   title = 'Total Income by Group')
        plt.show()
    