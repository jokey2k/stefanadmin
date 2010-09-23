#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flaskext.sqlalchemy import SQLAlchemy
from hashlib import md5

# configuration
SECRET_KEY = 'development key'
DEBUG = True
HOST = '127.0.0.1'

# Admin data
USERNAME='mySecretUser'
PASSWORD='mySecretPassword'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('STEFANADMIN_SETTINGS', silent=True)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/example.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://mail:mailpw@localhost/mail'
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
    _password = db.Column('password', db.String(32), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('virtual_domains.id'))
    domain = db.relationship(VirtualDomain, uselist=False, backref=db.backref('users',cascade="all, delete, delete-orphan"))

    def __init__(self, domain, email, password=u''):
        self.domain = domain
        self.email = email
        self.password = password

    @property
    def password(self):
        return self.password

    @password.setter
    def _set_password(self, password):
        self.password = md5(password).hexdigest()

    password = db.synonym('_password', descriptor=password)

    def check_password(self, password):
        return self.password == md5(password).hexdigest()

    def __repr__(self):
        return '<VirtualUser %r>' % self.username


class VirtualAlias(db.Model):
    __tablename__ = 'virtual_aliases'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('virtual_domains.id'))
    domain = db.relationship(VirtualDomain, uselist=False, backref=db.backref('aliases',cascade="all, delete, delete-orphan"))
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
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    domain = VirtualDomain(request.form['domainname'])
    db.session.add(domain)
    db.session.commit()
    flash('Domain added')
    return redirect(url_for('show_tree'))

@app.route('/domain/<int:domain_id>/del', methods=['GET'])
def del_domain(domain_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    domain = VirtualDomain.query.filter_by(id=domain_id).first() 
    db.session.delete(domain)
    db.session.commit()
    flash('Domain deleted')
    return redirect(url_for('show_tree'))

@app.route('/domain/<int:domain_id>/user/new', methods=['POST'])
def add_user(domain_id):
    print "Hello"
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    domain = VirtualDomain.query.get(domain_id)
    if domain is None:
        flash('Invalid domain id')
        return redirect(url_for('show_tree'))

    newuser = VirtualUser(domain, request.form['username'], request.form['password'])
    db.session.add(newuser)
    db.session.commit()
    flash('User added')
    return redirect(url_for('show_tree'))

@app.route('/domain/<int:domain_id>/user/<int:user_id>/del', methods=['GET'])
def del_user(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    user = VirtualUser.query.filter_by(id=user_id).first() 
    db.session.delete(user)
    db.session.commit()
    flash('User deleted')
    return redirect(url_for('show_tree'))

@app.route('/domain/<int:domain_id>/alias/new', methods=['POST'])
def add_alias(domain_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    domain = VirtualDomain.query.get(domain_id)
    if domain is None:
        flash('Invalid domain id')
        return redirect(url_for('show_tree'))

    newalias = VirtualAlias(domain, request.form['source'], request.form['destination'])
    db.session.add(newalias)
    db.session.commit()
    flash('Alias added')
    return redirect(url_for('show_tree'))

@app.route('/domain/<int:domain_id>/alias/<int:alias_id>/del', methods=['GET'])
def del_alias(alias_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    alias = VirtualAlias.query.filter_by(id=alias_id).first() 
    db.session.delete(alias)
    db.session.commit()
    flash('Alias deleted')
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
    app.run(debug=app.config['DEBUG'],host=app.config['HOST'])
