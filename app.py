from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_marshmallow import Marshmallow
import json, os
import boto3
from botocore.exceptions import NoCredentialsError
from configparser import ConfigParser
import logging

#app initialization
app = Flask(__name__)
app.secret_key = "Secret_Key" #session

#basic authentication
auth = HTTPBasicAuth()

#db connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/bankapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)

#write error log
logging.basicConfig(filename="log.txt",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.info)

#file upload from loacl to s3
def upload_to_aws(resp_json_file, bucket, s3path):
    try:
        s3resource.upload_file(resp_json_file, bucket, s3path)
        return "True"
    except FileNotFoundError:
        logging.error(f"Json file not found {resp_json_file}")
    except NoCredentialsError:
        logging.error(f"Access issue to upload the file")

#DB model creation
class Custdata(db.Model):
    customer_id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50))
    bank_name = db.Column(db.String(50))
    address = db.Column(db.String(100))
    contact = db.Column(db.Integer)
    account_type = db.Column(db.String(50))

    def __init__(self, name, bank_name, address, contact, account_type):
        self.name = name
        self.bank_name = bank_name
        self.address = address
        self.contact = contact
        self.account_type = account_type

with app.app_context():
    db.create_all()

#Data serializaion
class BankSchema(ma.Schema):
    class Meta:
        fields = ("customer_id", "name", "bank_name", "address", "contact", "account_type")

#custdata table schema
bank_schema = BankSchema()
bank_schema = BankSchema(many=True)

'''@app.route('/')
def display():
    return render_template("users.html")'''

'''@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        customer_id = request.form['id']
        user = Custdata.query.filter_by(customer_id = customer_id).first()
        if user == None:
            flash('User Exist')
            return "Welcome to Flask Application"
        else:
            flash('User does not exist')
            return "You are not an authourized person"'''

#Fetch all customer details
@app.route('/custdata', methods=['GET'])
def get_customer_details():
    all_data = Custdata.query.all()
    return bank_schema.jsonify(all_data)

#Add new customer details    
@app.route('/custdata', methods=['POST'])
def add_customer():
    if request.method == 'POST':
        name = request.json['name']
        bank_name = request.json['bank_name']
        address = request.json['address']
        contact = request.json['contact']
        account_type = request.json['account_type']

        new_data = Custdata(name, bank_name, address, contact, account_type)
        db.session.add(new_data)
        db.session.commit()
        return "Data added successfully"

#get specific customer data
@app.route("/custdata/<customer_id>", methods=["GET"])
def get_detail(customer_id):
    if request.method == 'GET':
        my_data = Custdata.query.filter_by(customer_id = customer_id)
        return bank_schema.jsonify(my_data)
        
#Update the existing customer details
@app.route("/custdata/<customer_id>", methods=['PUT'])
def update(customer_id):
    if request.method == 'PUT':
        my_data = Custdata.query.get(customer_id)
        my_data.name = request.json['name']
        my_data.bank_name = request.json['bank_name']
        my_data.address = request.json['address']
        my_data.contact = request.json['contact']
        my_data.account_type = request.json['account_type']

        db.session.commit()
        return "Data modified successfully"

#Delete the specific customer
@app.route('/custdata/<customer_id>', methods=['DELETE'])
def delete(customer_id):
    my_data = Custdata.query.get(customer_id)
    db.session.delete(my_data)
    db.session.commit()
    return f"Record {customer_id} deleted successfully"

#Read the config file
config_data = ConfigParser()
config_data.read("config.ini")
aws_access = config_data["AWSPARMS"]
s3resource = boto3.client("s3", aws_access_key_id=aws_access["accesskey"], aws_secret_access_key=aws_access["secretkey"])

#Get customer details and saved as a json file
#then upload to S3 buclet
@app.route("/json_resp", methods=["GET"])
def get_cust_details_and_upload_to_s3():
    try:
        all_cust_details = Custdata.query.all()
        result = bank_schema.dump(all_cust_details)

        resp_json_file = 'D:\\Flask_POC\\response\\resp.json'
        for item in result:
            output = json.dumps(item)

            with open(resp_json_file, "a+") as outfile:
                outfile.write(str(output))
                outfile.close()

        s3path = aws_access["s3path"] + "resp.json"
        bucket = aws_access["s3bucketname"]
        uploaded = upload_to_aws(resp_json_file, bucket, s3path)

        if uploaded == "True":
            os.remove(resp_json_file)
        else:
            logging.info("Could not unlink the json file")
        return "Json file created and uploaded to s3 bucket successfully"
    except Exception as e:
        return(f"Unable to fetch the Customer Details {e}")

#main function
if __name__ == "__main__":
    app.run(debug=True)
