from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Sequence
import secrets
from flask_migrate import Migrate
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)  

# Change this according to your local Postgres DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/postgres'


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

""" Common Tables - Authentication """
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(225), nullable=False)
    email = db.Column(db.String(225), unique=True, nullable=False)
    password = db.Column(db.String(225), nullable=False)
    department = db.Column(db.String(225), nullable=False)
    role = db.Column(db.String(225), nullable=False)
    department_id = db.Column(db.Integer(), db.ForeignKey('department.department_id'))

class UserActivity(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer())
    user_name = db.Column(db.String(225), nullable=False)
    user_department = db.Column(db.String(225), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    route_name = db.Column(db.String(225), nullable=False)
    activity_done = db.Column(db.String(1000), nullable=False)

class department_form_list(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    department_id = db.Column(db.Integer(), db.ForeignKey('department.department_id'))
    form_id = db.Column(db.Integer())
    form_name = db.Column(db.String(225))

class department(db.Model):
    department_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    department_name = db.Column(db.String(225))

""" Common Tables - Data """

class designations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True)

""" Form Tables """ 

class Csr_Activity(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    date_csr = db.Column(db.Date(),nullable=True) #date
    activity_name_csr = db.Column(db.String(255),nullable=True)
    amount_proposed_csr = db.Column(db.Integer(),nullable=True) #number
    amount_sanctioned_csr = db.Column(db.Integer(),nullable=True) #number
    sanctioned_party_name_csr = db.Column(db.String(255),nullable=True)
    sanctioned_date_csr = db.Column(db.Date(),nullable=True) #date
    upload_file_csr_path = db.Column(db.String(255),nullable=True) #file
    notified_date_csr = db.Column(db.Date(),nullable=True) #date
    approved_finance_csr = db.Column(db.String(255),nullable=True)
    approval_date_csr = db.Column(db.Date(),nullable=True) #date
    remarks_gad_csr = db.Column(db.String(5000),nullable=True)
    remarks_finance_csr = db.Column(db.String(5000),nullable=True)
    deleted = db.Column(db.Integer(), default=0)     

class FunctionHalls(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    function_hall_name = db.Column(db.String(255),nullable=True)
    alloted_to_party_name = db.Column(db.String(255),nullable=True)
    free_allotment = db.Column(db.String(255),nullable=True)
    reason_for_free_allotment = db.Column(db.String(255),nullable=True)
    revenue_rs = db.Column(db.String(255),nullable=True)
    deleted = db.Column(db.Integer(), default=0)

class NumOfDeaths(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    concerned_department = db.Column(db.String(255),nullable=True)
    post_category = db.Column(db.String(255),nullable=True)
    employee_code = db.Column(db.String(255),nullable=True)
    designation = db.Column(db.String(255),nullable=True)
    retirement_date = db.Column(db.Date(),nullable=True)
    upload_office_order_path = db.Column(db.String(255),nullable=True)
    employee_name = db.Column(db.String(255),nullable=True)
    payscale = db.Column(db.String(255),nullable=True)
    date_of_settlement = db.Column(db.Date(),nullable=True)
    num_of_death_cases = db.Column(db.String(255),nullable=True)
    deleted = db.Column(db.Integer(), default=0)

class Retirements(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    concerned_department = db.Column(db.String(255),nullable=True)
    post_category = db.Column(db.String(255),nullable=True)
    employee_code = db.Column(db.String(255),nullable=True)
    employee_name = db.Column(db.String(255),nullable=True)
    designation = db.Column(db.String(255),nullable=True)
    payscale = db.Column(db.String(255),nullable=True) 
    retirement_date = db.Column(db.Date(),nullable=True)
    residing_in_port_quaters = db.Column(db.String(255),nullable=True)
    remarks_by_gad = db.Column(db.String(255),nullable=True)
    remarks_by_finance = db.Column(db.String(255),nullable=True)
    deleted = db.Column(db.Integer(), default=0)
