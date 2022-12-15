from flask import Flask
from flask_mysqldb import MySQL
app=Flask(__name__)
msql = MySQL(app)
#db Confugurations
app.config['user-name'] = ''
app.config['password'] = ''
app.config['database'] = ''
app.config['localhost'] = ''

