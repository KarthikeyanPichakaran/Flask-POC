from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_marshmallow import Marshmallow


#app initialization
app = Flask(__name__)
app.secret_key = "Secret_Key" #session

#basic authentication
auth = HTTPBasicAuth()
users = {"flask": generate_password_hash("bankapp")}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

#data serializaion and deserialization
ma = Marshmallow(app)

class BankSchema(ma.Schema):
    class Meta:
        fields = ("customer_id", "name", "bank_name", "address", "contact", "account_type")

#custdata table schema
bank_schema = BankSchema()
bank_schema = BankSchema(many=True)

#db connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/bankapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

@app.route('/custdata', methods=['GET'])
@auth.login_required
def get_customer_details():
    all_data = Custdata.query.all()
    return bank_schema.jsonify(all_data) #API Json result
    #return render_template("Index.html", customers= all_data) #HTML result 

@app.route('/custdata', methods=['POST'])
def add_customer():
    if request.method == 'POST':
        #name = request.form['name']
        #bank_name = request.form['bname']
        #address = request.form['address']
        #contact = request.form['contact']
        #account_type = request.form['acctype']
        
        name = request.json['name']
        bank_name = request.json['bank_name']
        address = request.json['address']
        contact = request.json['contact']
        account_type = request.json['account_type']

        new_data = Custdata(name, bank_name, address, contact, account_type)
        db.session.add(new_data)
        db.session.commit()

        #flash("New Customer Added Successfully")
        return "Data added successfully"
        #return redirect(url_for('Index'))

#get particular customer data
@app.route("/custdata/<customer_id>", methods=["GET"])
def get_detail(customer_id):
    if request.method == 'GET':
        my_data = Custdata.query.filter_by(customer_id = customer_id)
        #print(my_data)
        return bank_schema.jsonify(my_data)
        
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
        #flash("Customer Data Updated Successfully")
        #return redirect(url_for('Index'))
        return "Data modified successfully"

@app.route('/custdata/<customer_id>', methods=['DELETE'])
def delete(customer_id):
    my_data = Custdata.query.get(customer_id)
    db.session.delete(my_data)
    db.session.commit()
    return "Data deleted successfully"
    #flash("Customer Data Deleted Successfully")
    #return redirect(url_for('Index'))

if __name__ == "__main__":
    app.run(debug=True)
