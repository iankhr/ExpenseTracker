# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 16:14:24 2019

@author: Ian
"""

import mysql.connector as sc
import pandas as pd
import numpy as np

try:
    credentials = open('info.creds', 'r')
    creds = credentials.read()
    credentials.close()
    creds = creds.strip().splitlines()
    USER = creds[0].split('=')[1].strip()
    PASSWORD = creds[1].split('=')[1].strip()
    HOST = creds[2].split('=')[1].strip()
    DATABASE = creds[3].split('=')[1].strip()
except:
    USER = 'user'
    PASSWORD = 'password'
    HOST ='127.0.0.1'
    DATABASE = 'expenses'


def insertTable(data, tbname):
    # creating list of fields to update
    cols = ["`"+str(item)+"`" for item in data.columns]
    cols = ','.join(cols)
    # creating text version of data
    textVals = ','.join(['('+','.join([nan4null(item) for item in data.iloc[i,:]]) + ')'\
                  for i in range(len(data))])
    # creating query
    sqlquery = 'INSERT INTO '+"`"+tbname+"`"+' ('+cols+')'
    # adding data to query
    sqlquery = sqlquery + ' VALUES '+textVals+';'
    return sqlquery

def insertData(data, tbname):
    # connecting to database and writing down the stockHeader database
    dbcnn = sc.connect(user = USER, password = PASSWORD,\
                       host = HOST, database = DATABASE)
    crs = dbcnn.cursor()
    try:
        # forming sql query here
        sqlquery = insertTable(data, tbname)
        # sending requests
        crs.execute(sqlquery)
        # making sure the information was inserted
        dbcnn.commit()
    finally:
        # closing connection
        crs.close()
        dbcnn.close()

def readData(tbname, where = None, order = None, sort = None, limit = None,\
             columns = None, group = None):
    # connecting to database and writing down the stockHeader database
    dbcnn = sc.connect(user = USER, password = PASSWORD,\
                       host = HOST, database = DATABASE)
    crs = dbcnn.cursor()
    try:
        # forming sql query here
        sqlquery = 'SELECT '
        if columns is None:
            sqlquery = sqlquery +'*'
        else:
            sqlquery = sqlquery + ','.join(columns)
        
        sqlquery = sqlquery+' FROM `'+str(tbname)+'`'
        if where is not None:
            sqlquery = sqlquery+' WHERE ' +where
        if order is not None:
            if len(order) > 1:
                sqlquery = sqlquery+' ORDER BY '+','.join(order)
            elif len(order) == 1:
                sqlquery = sqlquery+' ORDER BY '+order[0]
        if group is not None:
            if len(group) > 1:
                sqlquery = sqlquery+' ORDER BY '+','.join(group)
            elif len(group) == 1:
                sqlquery = sqlquery+' ORDER BY '+group[0]
        if sort is not None:
            if len(sort) > 1:
                sqlquery = sqlquery + 'SORT BY '+','.join(sort)
            elif len(sort)==1:
                sqlquery = sqlquery + 'SORT BY '+sort[0]
        if limit is not None:
            sqlquery = sqlquery + ' LIMIT '+str(limit)
        # sending requests
        crs.execute(sqlquery)
        result = crs.fetchall()
        if columns is None:
            sqlquery = 'DESCRIBE `'+str(tbname)+'`'
            crs.execute(sqlquery)
            cols = crs.fetchall()
            columns = [item[0] for item in cols]
        return pd.DataFrame(result, columns = columns)
    finally:
        # closing connection
        crs.close()
        dbcnn.close()

def nan4null(item):
    try:
        if np.isnan(item):
            return 'NULL'
        else:
            return "'"+str(item).replace("'",'')+"'"
    except:
        return "'"+str(item).replace("'",'')+"'"
    
def alterData(data, tbname, where):
    # connecting to database and writing down the stockHeader database
    dbcnn = sc.connect(user = USER, password = PASSWORD,\
                       host = HOST, database = DATABASE)
    crs = dbcnn.cursor()
    # creating text version of data
    cols = ["`"+str(item)+"`" for item in data.columns]
    textVals = [nan4null(item) for item in data.iloc[0,:]]
    textdata = [str(cols[i]) + '=' + str(textVals[i]) for i in range(len(cols))]
    #print(textdata)
    try:
        # forming sql query here
        sqlquery = 'UPDATE '+"`"+tbname+"`" +' SET ' \
                                            +','.join(textdata) + ' WHERE ' + where
        # sending requests
        crs.execute(sqlquery)
        # making sure the information was inserted
        dbcnn.commit()
    finally:
        # closing connection
        crs.close()
        dbcnn.close()
        