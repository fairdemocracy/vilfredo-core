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

from flask import session, request, make_response

from . import app, models, api

from database import db_session

from flask import render_template, url_for, redirect


def redirect_url():
    return request.args.get('next') or \
           request.referrer or \
           url_for('index')


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
    auth = request.cookies.get('vgaclient')
    if not auth:
        return redirect(redirect_url())
    else:
        return render_template("question.html")
        
@app.route('/invitation/<token>')
def add_invitation_from_token(token):
    auth = request.cookies.get('vgaclient')
    user = api.load_token(auth)
    if not user:
        return redirect(redirect_url())
    else:
        question_id = models.EmailInvite.accept(user, token)
        if question_id == False:
            return redirect(redirect_url())
        else:
            return redirect('/question/' + str(question_id))

@app.route('/resetpwd/<token>')
def reset_password_from_token(token):
    return render_template("resetpwd.html")

@app.route('/activate')
def activate():
    from .database import db_session
    redirect_to_index = redirect(url_for('index'))
    resp = make_response(redirect_to_index)
    user_id = request.args.get('u')
    token = request.args.get('t')
    verify = models.VerifyEmail.query.filter_by(user_id=user_id,token=token).first()

    if not user_id or not token:
        app.logger.debug("Account Activation: Token and user_id not in link...\n")
        resp.set_cookie('vgamessage', 'Sorry, that link is invalid!')
        resp.set_cookie('vgastatus', 'error')
        return resp

    if not verify:
        app.logger.debug("Account Activation: Token and user_id not listed...\n")
        resp.set_cookie('vgamessage', 'Sorry we have no record of you registration. Please register again.')
        resp.set_cookie('vgastatus', 'error')
        return resp

    elif models.get_timestamp() > verify.timeout:
        app.logger.debug("Account Activation: Token expired...\n")
        resp.set_cookie('vgamessage', 'Sorry, you took too long to activate your account. Please register again.')
        resp.set_cookie('vgastatus', 'error')
        # Delete validation entry
        db_session.delete(verify)
        db_session.commit()
        return resp

    user =  models.User.query.get(verify.user_id)
    if not user:
        app.logger.debug("Account Activation: Unknown user...\n")
        resp.set_cookie('vgamessage', 'Sorry we have no record of you registration. Please register again.')
        resp.set_cookie('vgastatus', 'error')
        # Delete validation entry
        db_session.delete(verify)
        db_session.commit()
        return resp

    # app.logger.debug("Account Activation: Success! User %s %s activated!\n" % str(user.id), user.username)
    # Delete validation entry
    db_session.delete(verify)
    db_session.commit()
    # Log user in
    auth_token = user.get_auth_token()
    resp.set_cookie('vgaclient', auth_token)
    resp.set_cookie('vgastatus', 'success')
    resp.set_cookie('vgamessage', 'Hey %s! Your account is now active. Welcome to Vilfredo!' % user.username)

    return resp


@app.route('/lostpassword')
def lost_password():
    return render_template("lostpassword.html")

@app.route('/domination/<int:question_id>/gen/<int:generation>')
def display_domination(question_id, generation):
    return render_template("domination.html")

