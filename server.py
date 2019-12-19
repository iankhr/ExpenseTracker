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
                           tables=[accounts.to_html(classes='data')],\
                           titles=accounts.columns.values)

@app.route('/_load_data')
def load_data():
    try:
        month = request.args.get('month')
        data = getCurrentMonthExpenses(month)
        data.sort_values(by='date', inplace = True, ascending = False)
        data.reset_index(inplace = True, drop=True)
        data.drop(['rowid',], axis=1, inplace =True)
        return jsonify(result = data.to_html(classes = 'data'))
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(host='127.0.0.2', port=port, debug=True)