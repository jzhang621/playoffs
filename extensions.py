from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:sandiego1858@playoffmysqldbinstance.cl2bfofuauia.us-west-1.rds.amazonaws.com:3306/playoffs'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost:3306/playoffs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
db.init_app(app)
db.app = app
