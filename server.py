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

app = Flask(__name__, static_url_path='')
port = int(os.getenv('PORT', 8000))   
   
@app.route('/')
def root():
    accounts = db.readData('accounts')
    #return app.send_static_file('index.html')
    return render_template('index.html',  tables=[accounts.to_html(classes='data')],\
                                            titles=accounts.columns.values)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)