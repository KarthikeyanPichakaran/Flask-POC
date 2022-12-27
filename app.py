"""Restful API for CRUD operation of Banking Customers"""
import json
import os
import datetime
from configparser import ConfigParser  # config file
from flask import (Flask, render_template, session, request, redirect, url_for, flash, g)  # flask framework
from flask_sqlalchemy import SQLAlchemy  # mysql db connection
from flask_httpauth import HTTPBasicAuth  # basic authentication
from flask_marshmallow import Marshmallow  # data serialization
import boto3  # aws service
from botocore.exceptions import NoCredentialsError  # aws service exceptions
from healthcheck import HealthCheck, EnvironmentDump #request and response health
# Documentation packages
from flasgger import Swagger  # api documentation
from flasgger.utils import swag_from  # decorator for an API
from flasgger import LazyString, LazyJSONEncoder  # swagger UI

curdata = datetime.datetime.today().strftime("%d%m%Y")

# app initialization
app = Flask(__name__)
app.secret_key = "Secret_Key"  # session

# basic authentication
auth = HTTPBasicAuth()

# db configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:" "@localhost/bankapp"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
health = HealthCheck()
envdump = EnvironmentDump()
envdump = EnvironmentDump(include_python=False, include_os=False, include_process=False)

# swagger configuration for API documentations
app.config["SWAGGER"] = {"title": "Flask Swagger-UI", "uiversion": 2}
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/",
}

template = dict(
    swaggerUiPrefix=LazyString(lambda: request.environ.get("HTTP_X_SCRIPT_NAME", ""))
)
app.json_encoder = LazyJSONEncoder
swagger = Swagger(app, config=swagger_config)

class Custdata(db.Model):
    """Model creation for customer data"""
    customer_id = db.Column(db.Integer, primary_key=True)
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

class BankSchema(ma.Schema):
    """Data serializaion"""
    class Meta:
        fields = (
            "customer_id",
            "name",
            "bank_name",
            "address",
            "contact",
            "account_type",
        )
# custdata table schema
bank_schema = BankSchema()
bank_schema = BankSchema(many=True)

# static log file created
log_file = "D:\\Flask_POC\\flaskpoc\\log\\error_log.txt"


def track_exception(err_msg):
    """log file creation
    Args:
        err_msg (string): log message
    """
    with open(log_file, "a+", encoding='utf-8') as er:
        er.write(err_msg)


def upload_to_aws(resp_json_file, bucket, s3path):
    """Json file uploaded into S3 bucket

    Args:
        resp_json_file (string): json file
        bucket (string): bucket name
        s3path (string): s3 path

    Returns:
        boolean: File upload success
    """
    try:
        s3resource.upload_file(resp_json_file, bucket, s3path)
        return "True"
    except FileNotFoundError:
        err_msg = f"Err: Json file not found {resp_json_file}"
        track_exception(err_msg)
    except NoCredentialsError:
        err_msg = f"Err: Access issue to upload the file"
        track_exception(err_msg)


@app.route("/", methods=["GET", "POST"])
def login():
    """User LogIn to access API 
    Returns:
        HTTP response/HTML template : Json response as customer details
         or HTML template
    """
    if request.method == "POST":
        cust_id = int(request.form["aid"])
        cdata = Custdata.query.get(cust_id)
        if cdata is not None:
            g.record = 1
            if "cust_id" in session:
                session.clear()
            all_data = Custdata.query.all()
            return bank_schema.jsonify(all_data)
        else:
            g.record = 0

        if g.record != 1:
            flash("Username and Account Id Mismatch...!!!", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/custdata", methods=["GET"])
@swag_from("swagger_doc.yaml")
def get_customer_details():
    """request to fetch the customer details
    Returns:
        response: JSON
    """
    try:
        all_data = Custdata.query.all()
        return bank_schema.jsonify(all_data)
    except Exception as get_err:
        err_msg = f"Err: GET customer details request error {get_err}"
        track_exception(err_msg)


@app.route("/custdata", methods=["POST"])
@swag_from("swagger_doc.yaml")
def add_customer():
    """request to create a new customer
    Returns:
        response: success message
    """
    try:
        if request.method == "POST":
            name = request.json["name"]
            bank_name = request.json["bank_name"]
            address = request.json["address"]
            contact = request.json["contact"]
            account_type = request.json["account_type"]

            new_data = Custdata(name, bank_name, address, contact, account_type)
            db.session.add(new_data)
            db.session.commit()
            return "Data added successfully"
    except Exception as post_err:
        err_msg = f"Err: Could not add new customer into the database {post_err}"
        track_exception(err_msg)


@swag_from("swagger_doc.yaml")
@app.route("/custdata/<customer_id>", methods=["GET"])
def get_detail(customer_id):
    """request to get the specific customer details
    Args:
        customer_id (integer): to retrive the specific customer details
    Returns:
        response: JSON response(as a specific customer details)
    """
    try:
        if request.method == "GET":
            my_data = Custdata.query.filter_by(customer_id=customer_id)
            return bank_schema.jsonify(my_data)
    except Exception as id_err:
        err_msg = f"Err: Could not get the specific customer details {id_err}"
        track_exception(err_msg)


@app.route("/custdata/<customer_id>", methods=["PUT"])
@swag_from("swagger_doc.yaml")
def update(customer_id):
    """request to update the existing customer details
    Args:
        customer_id (integer): update the specific customer details
    Returns:
        response: message
    """
    try:
        if request.method == "PUT":
            my_data = Custdata.query.get(customer_id)
            my_data.name = request.json["name"]
            my_data.bank_name = request.json["bank_name"]
            my_data.address = request.json["address"]
            my_data.contact = request.json["contact"]
            my_data.account_type = request.json["account_type"]

            db.session.commit()
            return "Data modified successfully"
    except Exception as updt_err:
        err_msg = f"Err: Could not update the existing customer details {updt_err}"
        track_exception(err_msg)


@app.route("/custdata/<customer_id>", methods=["DELETE"])
@swag_from("swagger_doc.yaml")
def delete(customer_id):
    """request to delete the specific customer details
    Args:
        customer_id (integer): to delete the specific customer details
    Returns:
        response: success message
    """
    try:
        my_data = Custdata.query.get(customer_id)
        db.session.delete(my_data)
        db.session.commit()
        return f"Record {customer_id} deleted successfully"
    except Exception as del_err:
        err_msg = f"Err: Could not delte the customer details {del_err}"
        track_exception(err_msg)

# Read the config file
config_data = ConfigParser()
config_data.read("config.ini")
aws_access = config_data["AWSPARMS"]
s3resource = boto3.client(
    "s3",
    aws_access_key_id=aws_access["accesskey"],
    aws_secret_access_key=aws_access["secretkey"],
)

@app.route("/json_resp", methods=["GET"])
def get_cust_details_and_upload_to_s3():
    """this request to get the customer details as a JSON response
     and saved it in a local and upload into S3 bucket
    Returns:
        response: success message
    """
    try:
        all_cust_details = Custdata.query.all()
        result = bank_schema.dump(all_cust_details)

        resp_json_file = "D:\\Flask_POC\\flaskpoc\\response\\resp.json"
        for item in result:
            output = json.dumps(item)

            with open(resp_json_file, "a+", encoding='utf-8') as outfile:
                outfile.write(str(output))

        s3path = aws_access["s3path"] + f"Resp_JSON/resp.json_{curdata}"
        bucket = aws_access["s3bucketname"]
        uploaded = upload_to_aws(resp_json_file, bucket, s3path)

        if uploaded == "True":
            os.remove(resp_json_file)
            return "Json file created and uploaded to s3 bucket successfully"
        else:
            err_msg = (
                f"Err: Could not upload the json file into s3 bucket {resp_json_file}"
            )
            track_exception(err_msg)
    except Exception as dat_err:
        err_msg = f"Err: Unable to fetch the Customer Details {dat_err}"
        track_exception(err_msg)


# If log file is exists upload to S3 bucket
s3path = aws_access["s3path"]
bucket = aws_access["s3bucketname"]
if os.path.exists(log_file):
    uploaded = upload_to_aws(log_file, bucket, s3path + f"Error_Log/log.txt_{curdata}")
    os.remove(log_file)
else:
    next

health.add_check(get_cust_details_and_upload_to_s3)
health.add_check(add_customer)
health.add_check(get_detail)
health.add_check(update)
health.add_check(delete)

# Add a flask route to expose information
app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: health.run())

# main function
if __name__ == "__main__":
    """run flask application"""
    app.run(debug=True)
