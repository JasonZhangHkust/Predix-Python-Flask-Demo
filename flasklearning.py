from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
from flask import request, redirect, url_for, flash
from flask_httpauth import HTTPBasicAuth
from sqlalchemy.exc import IntegrityError, DataError
from wtforms import Form, StringField, validators, IntegerField, RadioField
from wtforms.validators import DataRequired, Length
from flask_bootstrap import Bootstrap
import ConfigParser
import os

app = Flask(__name__)
bootstrap = Bootstrap(app)
auth = HTTPBasicAuth()
curr_dir = os.path.dirname(os.path.realpath(__file__))
config_file = curr_dir + os.sep + "config.conf"
cf = ConfigParser.ConfigParser()
cf.read(config_file)
myUri = cf.get('db', 'uri')
port = int(os.getenv("PORT", 3000))
app.config['SECRET_KEY'] = '123456'
app.config['SQLALCHEMY_DATABASE_URI'] = myUri   #'postgresql://postgres:123478@localhost/person'
app.debug = True
app.config.update(dict(
  PREFERRED_URL_SCHEME='https'
))
users = [
    {'username': 'admin', 'password': 'predixFlask'}
]
db = SQLAlchemy(app)


class User(db.Model): # User data model
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    gender = db.Column(db.String(10), unique=False)
    age = db.Column(db.Integer, unique=False)
    college = db.Column(db.String(120),unique=False)

    def __init__(self, username, gender, age, college):
        self.username = username
        self.gender = gender
        self.age = age
        self.college = college

    def __repr__(self):
        return '<User %r>' % self.username


@auth.get_password
def get_password(username):
    for user in users:
        if user['username'] == username:
            return user['password']
    return None


class RegistrationForm(Form): # Form Validation check
    username = StringField('username', validators=[Length(min=4, max=25)])
    gender = RadioField('gender', choices=[('Male', 'Male'), ('Female', 'Female')],
                        validators=[DataRequired(message=u'Please select your gender')])
    age = IntegerField('age', [validators.NumberRange(min=0, max=200)])
    college = StringField('college', [validators.Length(min=2, max=200)])


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ))


@app.route('/')
@auth.login_required
def index():
    return render_template('add_user.html')


@app.route('/profile/<username>', methods=['GET'])
@auth.login_required
def profile(username):  # retrieve user info from dynamic url
    user = User.query.filter_by(username=username).first()
    return render_template('profile.html', user=user)


@app.route('/profile', methods=['GET'])  # retrieve single user info with get method
def get_user():
    myUser = User.query.filter_by(username=request.args.get('username')).all()
    if myUser:
        return render_template('profile.html', myUser=myUser)
    else:
        flash('No Such Person', 'error')
        return redirect(url_for('index',_external=True, _scheme='https'))


@app.route('/profile/all', methods=['GET'])  # retrieve all users' info with get method
@auth.login_required
def get_all():
    myUser = User.query.all()
    if not myUser:
        flash('Database Empty', 'error')
        return redirect(url_for('index', _external=True, _scheme='https'))
    else:
        return render_template('profile.html', myUser=myUser)


@app.route('/post_user', methods=['POST']) #input user info with post method
def post_user():
    form = RegistrationForm(request.form)
    if not form.validate():
        flash_errors(form)
        return redirect(url_for('index',_external=True, _scheme='https'))
    user = User(form.username.data, form.gender.data, form.age.data, form.college.data)
    try:
        db.session.add(user)
        db.session.commit()
        flash('Adding Successfully', 'success')
    except IntegrityError:  # avoid duplicate name
        db.session.rollback()
        flash('Duplicate name, please try again', 'error')
    return redirect(url_for('index',_external=True, _scheme='https'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
