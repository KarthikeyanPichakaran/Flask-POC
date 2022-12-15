import pymysql
from app import app
from tables import Results
from db_config import mysql
from flask import flash, render_template, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/new_user')
def add_user_view():
    return render_template('add_user.html')

@app.route('/add', methods=['POST'])
def add_user():
    pass

@app.route('/update/<int:id>')
def update_user():
    pass

@app.route('/delete/<int:id>')
def delete_user(id):
    pass

if __name__ == "__main__":
    app.run()