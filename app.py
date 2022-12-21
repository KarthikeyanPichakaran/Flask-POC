from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response,g
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_marshmallow import Marshmallow
import json, os
import boto3
from botocore.exceptions import NoCredentialsError
from configparser import ConfigParser
import logging
from flasgger import Swagger
#from flasgger.utils import swag_from
#from flasgger import LazyString, LazyJSONEncoder

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

#static log file created
log_file = "D:\\Flask_POC\\flaskpoc\\log\\error_log.txt"
def track_exception(err_msg):
    with open(log_file, "a+") as er:
        er.write(err_msg)
logging.basicConfig(filename="D:\\Flask_POC\\flaskpoc\log\logger.txt", filemode='a', level=logging.INFO)

#API documentations
app.config['SWAGGER'] = {
"swagger_version": "2.0",
"specs": [
{
"version": "0.0.1",
"title": "Api v1",
"endpoint": 'v1_spec',
"route": '/v1/spec',}]
}

swagger = Swagger(app)


#file upload from loacl to s3
def upload_to_aws(resp_json_file, bucket, s3path):
    try:
        s3resource.upload_file(resp_json_file, bucket, s3path)
        return "True"
    except FileNotFoundError:
        err_msg = (f"Err: Json file not found {resp_json_file}")
        track_exception(err_msg)
    except NoCredentialsError:
        err_msg = (f"Err: Access issue to upload the file")
        track_exception(err_msg)

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

#User LogIn to access API
@app.route('/', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            #uname = request.form['uname']
            cust_id = int(request.form['aid'])
            cdata = Custdata.query.filter_by(customer_id = cust_id)
            res = bank_schema.jsonify(cdata)
            redata = json.dumps(str(res))
            logging.info(f"The details are {type(res)} {type(redata)}")
            logging.info(f"The details are {res}, {redata}, {str(cdata)}, {cdata.json}")
            #for item in res:
            if redata[0]:
                g.record = 1
                all_data = Custdata.query.all()
                return bank_schema.jsonify(all_data)
            else:
                g.record = 0
    
            if g.record !=1:
                flash("Username and Account Id Mismatch...!!!", 'danger')
                return redirect(url_for('login'))
    except:
        err_msg = ("Err: Login issue please check the customer input")
        track_exception(err_msg)
    return render_template("login.html")
#Fetch all customer details
@app.route('/custdata', methods=['GET'])
def get_customer_details():
    try:
        all_data = Custdata.query.all()
        return bank_schema.jsonify(all_data)
    except Exception as get_err:
        err_msg = (f"Err: GET customer details request error {get_err}")
        track_exception(err_msg)

#Add new customer details    
@app.route('/custdata', methods=['POST'])
def add_customer():
    try:
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
    except Exception as post_err:
        err_msg = (f"Err: Could not add new customer into the database {post_err}")
        track_exception(err_msg)

#get specific customer data
@app.route("/custdata/<customer_id>", methods=["GET"])
def get_detail(customer_id):
    try:
        if request.method == 'GET':
            my_data = Custdata.query.filter_by(customer_id = customer_id)
            return bank_schema.jsonify(my_data)
    except Exception as err:
        err_msg = (f"Err: Could not get the specific customer details {err}")
        track_exception(err_msg)

#Update the existing customer details
@app.route("/custdata/<customer_id>", methods=['PUT'])
def update(customer_id):
    try:
        if request.method == 'PUT':
            my_data = Custdata.query.get(customer_id)
            my_data.name = request.json['name']
            my_data.bank_name = request.json['bank_name']
            my_data.address = request.json['address']
            my_data.contact = request.json['contact']
            my_data.account_type = request.json['account_type']

            db.session.commit()
            return "Data modified successfully"
    except Exception as updt_err:
        err_msg = (f"Err: Could not update the existing customer details {updt_err}")
        track_exception(err_msg)

#Delete the specific customer
@app.route('/custdata/<customer_id>', methods=['DELETE'])
def delete(customer_id):
    try:    
        my_data = Custdata.query.get(customer_id)
        db.session.delete(my_data)
        db.session.commit()
        return f"Record {customer_id} deleted successfully"
    except Exception as del_err:
        err_msg = (f"Err: Could not delte the customer details {del_err}")
        track_exception(err_msg)

#Read the config file
config_data = ConfigParser()
config_data.read("config.ini")
aws_access = config_data["AWSPARMS"]
s3resource = boto3.client("s3", aws_access_key_id=aws_access["accesskey"], aws_secret_access_key=aws_access["secretkey"])

#Get customer details and saved as a json file
#then upload to S3 bucket
@app.route("/json_resp", methods=["GET"])
def get_cust_details_and_upload_to_s3():
    try:
        all_cust_details = Custdata.query.all()
        result = bank_schema.dump(all_cust_details)

        resp_json_file = 'D:\\Flask_POC\\flaskpoc\\response\\resp.json'
        for item in result:
            output = json.dumps(item)

            with open(resp_json_file, "a+") as outfile:
                outfile.write(str(output))
                
        s3path = aws_access["s3path"] + "resp.json"
        bucket = aws_access["s3bucketname"]
        uploaded = upload_to_aws(resp_json_file, bucket, s3path)

        if uploaded == "True":
            os.remove(resp_json_file)
            return "Json file created and uploaded to s3 bucket successfully"
        else:
            err_msg = (f"Err: Could not upload the json file into s3 bucket {resp_json_file}")
            track_exception(err_msg)
    except Exception as e:
        err_msg = (f"Err: Unable to fetch the Customer Details {e}")
        track_exception(err_msg)

#main function
if __name__ == "__main__":
    app.run(debug=True)
