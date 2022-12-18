from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

#app initialization
app = Flask(__name__)
app.secret_key = "Secret_Key" #session

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

@app.route('/')
def Index():
    #return "Hello Flask Application"
    all_data = Custdata.query.all()
    return render_template("Index.html", customers= all_data)

@app.route('/insert', methods=['POST'])
def insert():
    if request.method == 'POST':
        name = request.form['name']
        bank_name = request.form['bname']
        address = request.form['address']
        contact = request.form['contact']
        account_type = request.form['acctype']
        
        my_data = Custdata(name, bank_name, address, contact, account_type)
        db.session.add(my_data)
        db.session.commit()

        flash("New Customer Added Successfully")

        return redirect(url_for('Index'))

@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        my_data = Custdata.query.get(request.form.get('customer_id'))
        my_data.name = request.form['name']
        my_data.bank_name = request.form['bank_name']
        my_data.address = request.form['address']
        my_data.contact = request.form['contact']
        my_data.account_type = request.form['account_type']

        db.session.commit()
        flash("Customer Data Updated Successfully")
        return redirect(url_for('Index'))

@app.route('/delete/<customer_id>', methods=['GET', 'POST'])
def delete(customer_id):
    my_data = Custdata.query.get(customer_id)
    db.session.delete(my_data)
    db.session.commit()
    flash("Customer Data Deleted Successfully")
    return redirect(url_for('Index'))

if __name__ == "__main__":
    app.run(debug=True) #publish your application
