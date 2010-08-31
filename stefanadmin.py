# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flaskext.sqlalchemy import SQLAlchemy
from hashlib import md5

# configuration
SECRET_KEY = 'development key'
DEBUG = True

# Admin data
USERNAME='mySecretUser'
PASSWORD='mySecretPassword'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('STEFANADMIN_SETTINGS', silent=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/example.db'
db = SQLAlchemy(app)

# DB Models
class VirtualDomain(db.Model):
    __tablename__ = 'virtual_domains'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __init__(self, name):
        self.name = name


class VirtualUser(db.Model):
    __tablename__ = 'virtual_users'
    id = db.Column(db.Integer, primary_key=True)
    _password = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('virtual_domains.id'))
    domain = db.relationship(VirtualDomain, uselist=False, backref=db.backref('users'))

    def __init__(self, domain, email, password=u''):
        self.domain = domain
        self.email = email
        self.set_password(password)

    def _set_password(self, password):
        self._password = md5(password).hexdigest()

    def _get_password(self):
        return self._password
    password = property(_get_password, _set_password)

    def check_password(self, password):
        return self.password == md5(password).hexdigest()

    def __repr__(self):
        return '<VirtualUser %r>' % self.username


class VirtualAlias(db.Model):
    __tablename__ = 'virtual_aliases'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('virtual_domains.id'))
    domain = db.relationship(VirtualDomain, uselist=False, backref=db.backref('aliases'))
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)

    def __init__(self, domain, source, destination):
        self.domain = domain
        self.source = source
        self.destination = destination


# View functions
@app.route('/')
def show_tree():
    """Render a simple tree showing all elements"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    domains = VirtualDomain.query.order_by(VirtualDomain.name).all()

    return render_template('show_tree.html', domains=domains)

@app.route('/domain/new', methods=['POST'])
def add_domain():
    flash('Domain added')
    return redirect(url_for('show_tree'))

@app.route('/domain/<int:domain_id>/user/new', methods=['POST'])
def add_user():
    flash('User added')
    return redirect(url_for('show_tree'))

@app.route('/domain/<int:domain_id>/alias/new', methods=['POST'])
def add_alias():
    flash('Alias added')
    return redirect(url_for('show_tree'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_tree'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_tree'))


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])