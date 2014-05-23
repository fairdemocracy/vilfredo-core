#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of VilfredoReloadedCore.
#
# Copyright (c) 2013 Derek Paterson <athens_code@gmx.com>
#
# VilfredoReloadedCore is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation version 3 of the License.
#
# VilfredoReloadedCore is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with VilfredoReloadedCore.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


'''
The Views
'''

from flask import session, request

from . import app, models

from .database import db_session

from flask import render_template


# @app.route('/', methods=['GET', 'POST'])
# @app.route('/index', methods=['GET', 'POST'])
# def index():
#    return "No questions here so far"
@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/question/<int:question_id>')
def display_question(question_id):
    return render_template("question.html")

@app.route('/graphs/<int:question_id>')
def display_graphs(question_id):
    return render_template("graphs.html")


@app.route('/register', methods=['GET', 'POST'])
def regiister():
    if request.method == 'POST':
        if request.form['username'] == '':
            return 'Invalid username'
        elif request.form['password'] == '':
            return 'Invalid password'
        elif request.form['email'] == '':
            return 'Invalid email'
        elif models.User.username_available(request.form['username']) \
                is not True:
            return 'Username not available'
        elif models.User.email_available(request.form['email']) is not True:
            return 'Email not available'
        else:
            new_user = models.User(
                request.form['username'],
                request.form['email'],
                request.form['password'])
            db_session.add(new_user)
            db_session.commit()
            if (new_user.id is not None):
                return 'You have been registered'
            else:
                return "Registration failed"
    return "Please enter your registration details"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] != 'test_user':
            return 'Invalid username'
        elif request.form['password'] != 'test_password':
            return 'Invalid password'
        else:
            session['logged_in'] = True
            return 'You were logged in'
    return "Please log in"


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return 'You were logged out'
