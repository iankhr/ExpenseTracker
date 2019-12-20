# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 20:33:25 2019

@author: Ian
"""

import pandas as pd
import os
import numpy as np
import localdb as db
from flask import Flask, render_template, request, jsonify
from main import getCurrentMonthExpenses, aggregateExpenses

app = Flask(__name__, static_url_path='')
port = int(os.getenv('PORT', 8000))   

def dftohtml(dftable, columns = None, tags = None, classes = None,\
             add_head = True, custom_columns = None):
    """
    This is a custom function to convert DataFrame to html and further pass it 
    to the website part.
    
    In this way I can add extra tags for future ability to edit data from the
    browser
    """
    # check whether it's dataframe
    if type(dftable) != pd.DataFrame:
        raise ValueError('Table must be DataFrame!')
    
    # check whether only certain data is needed        
    if columns is None:
        columns = dftable.columns
    
    # check whether the amount of custom columns matches the columns    
    if custom_columns is not None:
        if len(custom_columns) != len(columns):
            raise ValueError('Length of the custom columns does not match the amount of columns!')
    
    # open table tag
    htmlstr = '<table'
    if classes is not None:
        htmlstr = htmlstr + ' class ="{}"'.format(classes)
    htmlstr = htmlstr+'>'
    
    # add head of the table
    if add_head:
        htmlstr = htmlstr + '<thead><tr>'
        if custom_columns is None:
            htmlstr = htmlstr + ''.join(['<th>'+str(item)+'</th>'\
                                         for item in columns])
        else:
            htmlstr = htmlstr + ''.join(['<th>'+str(item)+'</th>'\
                                         for item in custom_columns])
            
        htmlstr = htmlstr + '</tr></thead>'
    
    # add content
    htmlstr = htmlstr + ''.join(['<tr>'+''.join(\
                    ['<td>'+str(element)+'</td>' for element in item]\
                    )+'</tr>' for item in dftable.loc[:,columns].values.tolist()])
    # close table tag
    htmlstr = htmlstr+'</table>'
    return htmlstr

@app.route('/')
def root():
    # read accounts
    accounts = db.readData('accounts')
    # read expenses
    expenses = getCurrentMonthExpenses()
    expenses['date'] = pd.to_datetime(expenses['date'])
    # extract available dates
    dates = expenses.resample('M', convention = 'end', on='date').last()
    dates = dates['date'].values
    dates = [str(pd.to_datetime(item).month) +'/'+str(pd.to_datetime(item).year) for item in dates]
    # reverse order so that latest are at the beginning
    dates = dates[::-1]
    return render_template('index.html',  dates = dates,\
                           tables=[accounts.to_html(classes='data',\
                           columns=['date', 'account', 'balance'])],\
                           titles=accounts.columns.values)

@app.route('/_load_data')
def load_data():
    try:
        month = request.args.get('month')
        # get value for internal accounting
        internalchk = request.args.get('inacc')
        if month == '-':
            return jsonify(result = '')
        else:
            data = getCurrentMonthExpenses(month)
            # aggregate expenses
            NetExpenses, totalExpenses, totalIncome = aggregateExpenses(data)
            data.sort_values(by='date', inplace = True, ascending = False)
            data.reset_index(inplace = True, drop=True)
            data.drop(['rowid',], axis=1, inplace =True)
            # change categories from numbers to text
            categories = db.readData('categories')
            categories.set_index('categoryid', inplace= True)
            data = data.join(categories, on = 'category')
            if internalchk == 'false':
                data = data[data['category'] != 16]
                
            return jsonify(result = dftohtml(data,\
                           classes = 'table table-brodered table-striped table-hover',\
                           columns = ['date','account','amount','msg',\
                                      'categoryname'],\
                           custom_columns = ['Date','Account', 'Amount, SEK',\
                                'Description', 'Category']),\
                           stats = dftohtml(totalExpenses,\
                           columns = ['categoryname','amount', 'monthlyLimit'],\
                           classes = 'table table-brodered table-striped table-hover',\
                           custom_columns = ['Category', 'Net Expsenses',\
                                             'Monthly limit']))
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(host='127.0.0.2', port=port, debug=True)