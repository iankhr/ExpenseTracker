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
from bs4 import BeautifulSoup as bs

app = Flask(__name__, static_url_path='')
port = int(os.getenv('PORT', 8000))   

def dftohtml(dftable, columns = None, classes = None,\
             add_head = True, custom_columns = None, index_on = None):
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
    if index_on is None:
        htmlstr = htmlstr + ''.join(['<tr>'+''.join(\
                ['<td>'+str(element)+'</td>' for element in item]\
                )+'</tr>' for item in dftable.loc[:,columns].values.tolist()])
    elif index_on == 'index':
        for i in dftable.index:
            htmlstr = htmlstr + '<tr id="index_{}">'.format(i)
            for j in dftable.loc[i,columns].values.tolist():
                htmlstr = htmlstr + '<td>' + str(j) + '</td>'
            
            htmlstr = htmlstr + '</tr>'
    else:
        for i in dftable[index_on].values.tolist():
            htmlstr = htmlstr + '<tr id="{}_{}">'.format(index_on,i)
            for j in dftable.loc[dftable[index_on]==i,columns].values[0]:
                htmlstr = htmlstr + '<td>' + str(j) + '</td>'
            
            htmlstr = htmlstr + '</tr>'    
        
    
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
    """
    Function that loads transaction data from the database
    """
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
            # data.drop(['rowid',], axis=1, inplace =True)
            # change categories from numbers to text
            categories = db.readData('categories')
            categories.set_index('categoryid', inplace= True)
            data = data.join(categories, on = 'category')
            # check whether to show internal accounting
            if internalchk == 'false':
                data = data[data['category'] != 16]
            
            # add addtional column with edit column 
            data['editData'] = ['<button class="btn btn-link" value="rowid_{}" onclick="editRow(this.value,0)">'.format(\
                                 data.loc[i,'rowid'])+\
                                'Edit</button>' for i in data.index]
            return jsonify(result = dftohtml(data,\
                           classes = 'table table-brodered table-striped table-hover',\
                           columns = ['date','account','amount','msg',\
                                      'categoryname', 'editData'],\
                           custom_columns = ['Date','Account', 'Amount, SEK',\
                                'Description', 'Category', ''],\
                           index_on = 'rowid'),\
                           stats = dftohtml(totalExpenses,\
                           columns = ['categoryname','amount', 'monthlyLimit'],\
                           classes = 'table table-brodered table-striped table-hover',\
                           custom_columns = ['Category', 'Net Expsenses',\
                                             'Monthly limit']))
    except Exception as e:
        return str(e)

@app.route('/_edit_data')
def edit_data():
    """
    the function returns an input field with the data to edit and two buttons
    save, cancel and a checkbox make a rule (default unchecked)
    """
    #try:
    action = int(request.args.get('action'))
    rowid = request.args.get('dataid')
    rowtext = request.args.get('rowtext')
    date = request.args.get('date')
    account = request.args.get('account')
    amount = request.args.get('amount')
    msg = request.args.get('msg')
    cat = request.args.get('cat')
    categories = db.readData('categories')
    dataText = [date,account,amount,msg,cat]
    if action == 0:
        # for each td insert an input field
        cols = rowtext.split('</td>')
        cols = [item.replace('<td>','') for item in cols]
        # remove last elements
        cols = cols[:-2]
        catNum = categories.loc[categories['categoryname'].apply(lambda x: x.upper())\
                            == cols[-1].upper(),\
                            'categoryid'].values[0]
        # add input fields
        """
        Make separate inputs for date and category
        """
        result = ['<td><input type = "date" id="{}_input_{}" value = "{}"></input></td>'.format(0,rowid,cols[0])]
        result = result + ['<td><input type = "text" id="{}_input_{}" value = "{}"></input></td>'.format(i,rowid,cols[i])\
                  for i in range(len(cols)) if (i>0) & (i<(len(cols)-1))]
        selectList = ['<option selected = "selected" value = "{}">'.format(\
                      cols[-1])+cols[-1]+'</option>']
        selectList = selectList+['<option value = {}>'.format(\
                      categories.loc[i,'categoryname'])\
                      +categories.loc[i,'categoryname']+'</option>'\
                      for i in range(len(categories))\
                      if categories.loc[i,'categoryid']!=catNum]
        result = result + ['<td><select>'+''.join(selectList)+'<select></td>']
        result = ''.join(result)
        # add buttons
        result = result+'<td><button class="btn btn-link" value="{}" onclick="editRow(this.value,1)">Cancel</button>'.format(rowid)\
               + '<button class="btn btn-link" value="{}" onclick="editRow(this.value,2)">Save</button>'.format(rowid)+'</td>'
    elif action == 1:
        # for each td insert an input field
        cols = rowtext.split('</td>')
        cols = [item.replace('<td>','') for item in cols]
        # remove last elements
        cols = cols[:-2]
        category = bs(cols[-1]).find('option').attrs['value']
        # extract values from input elements
        cols = [bs(item).find('input').attrs['value'] for item in cols if 'input' in item]
        cols = cols + [category,]
        # add back td and tr
        cols = ['<td>'+item+'</td>' for item in cols]
        # form html string
        result = ''.join(cols)
        # add back edit button
        result = result + '<td><button class="btn btn-link" value="{}" onclick="editRow(this.value, 0)">'.format(\
                                 rowid)+\
                                'Edit</button></td>'
    elif action == 2:
        catNum = categories.loc[categories['categoryname'].apply(lambda x: x.upper())\
                            == cat.upper(),\
                            'categoryid'].values[0]
        # create an update dataframe
        data = pd.DataFrame([date,account,amount,msg,catNum], index = ['date',\
                            'account', 'amount', 'msg', 'category']).T
        # update data
        db.alterData(data, 'transactions', where =\
                     'rowid = {}'.format(rowid.split('_')[-1]))
        # create result
        result = '<tr id = "{}">'.format(rowid)
        cols = ['<td>'+item+'</td>' for item in dataText]
        result = result + ''.join(cols)
        # add back edit button
        result = result + '<td><button class="btn btn-link" value="{}" onclick="editRow(this.value, 0)">'.format(\
                    rowid)+\
                    'Edit</button></td>'
        result = result+'</tr>'
        
    return jsonify(result = result)
   # except Exception as e: 
    #    return str(e)
    

if __name__ == '__main__':
    app.run(host='127.0.0.2', port=port, debug=True)