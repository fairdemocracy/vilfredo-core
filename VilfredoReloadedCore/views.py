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


@app.route('/domination/<int:question_id>/gen/<int:generation>')
def display_domination(question_id, generation):
    return render_template("domination.html")

