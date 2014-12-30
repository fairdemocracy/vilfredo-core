#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of VilfredoReloadedCore.
#
# Copyright © 2009-2013 Pietro Speroni di Fenizio / Derek Paterson.
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
Emails
'''

from . import app
from email.mime.text import MIMEText
from subprocess import Popen, PIPE
import os

def send_email(subject, sender_email, recipient_email, text_body):
    if os.environ.get('EMAIL_OFF', '0') == '0':
        msg = MIMEText(text_body)
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        p = Popen(["/usr/sbin/sendmail", "-t"], stdin=PIPE)
        p.communicate(msg.as_string())
        return p.returncode
    else:
        app.logger.debug("emails.send_email: EMAIL_OFF is set - no email sent!")
        return 1

def send_email_invite_accepted_email(user, email, question):
    '''
    .. function:: send_email_verification(email, token)

    Send an email containing a link to allow someone to reset their password.

    :param user: question participant
    :type user: User
    :param question: question
    :type toquestionken: Question
    :rtype: long
    '''
    body_template = \
    """
    The invitation you sent to %s for question "%s" has been accepted.
    
    http://%s/question/%s
    """
    return send_email("Vilfredo - Invitation Accepted",
                      app.config['ADMINS'][0],
                      user.email,
                      body_template % (email, question.title, app.config['SITE_DOMAIN'], question.id))

def send_moved_on_email(user, question):
    '''
    .. function:: send_email_verification(email, token)

    Send an email containing a link to allow someone to reset their password.

    :param user: question participant
    :type user: User
    :param question: question
    :type toquestionken: Question
    :rtype: long
    '''
    body_template = \
    """
    The question titled "%s" has now moved on to the %s stage.
    
    http://%s/question/%s
    """
    return send_email("Vilfredo - Question %s Now %s" % (question.title, question.phase),
                      app.config['ADMINS'][0],
                      user.email,
                      body_template % (question.title, question.phase, app.config['SITE_DOMAIN'], question.id))

def send_email_verification(user_id, email, token):
    '''
    .. function:: send_email_verification(email, token)

    Send an email containing a link to allow someone to reset their password.

    :param email: user email address
    :type email: string
    :param token: verification token
    :type token: string
    :rtype: long
    '''
    body_template = \
    """
    Welcome to Vilfrdo! Great to have you with us!
    
    Click on the link below to activate your account.
    
    Activate Account: http://%s
    """
    return send_email("Vilfredo - Activate Your Account",
                      app.config['ADMINS'][0],
                      email,
                      body_template % (app.config['SITE_DOMAIN']+'/activate'+'?u='+str(user_id)+'&t='+str(token)))

def send_password_reset_email(email, token):
    '''
    .. function:: send_password_reset_email(email, token)

    Send an email containing a link to allow someone to reset their password.

    :param email: receiver email address
    :type email: string
    :param token: password reset token
    :type token: string
    :rtype: long
    '''
    body_template = \
    """
    Click on the link below to enter a new password.
    
    Reset Password: http://%s
    """
    return send_email("Vilfredo - Password Reset Request",
                      app.config['ADMINS'][0],
                      email,
                      body_template % (app.config['SITE_DOMAIN']+'/resetpwd/'+token))

def send_question_email_invite_email(sender, recipient_email, question, token):
    '''
    .. function:: send_question_email_invite_email(sender, recipient_email, question, token)

    Send an email containing a link to allow someone to participate in a question.

    :param sender: User sending the invitation
    :type email: User
    :param recipient_email: recipient email address
    :type recipient_email: string
    :param question: The question the recipient is being invited to participate in
    :type question: Question
    :param token: email invitation token
    :type token: string
    :rtype: long
    '''
    # print "Sending email:", sender.username, question.title
    body_template = \
    """
    Vilfredo user %s invites you to participate in the question "%s".
    
    If you are already a member of Vilfredo please sign in then click on the Join Question link below.
    
    If you are not yet signed up then please go here http://%s and create an account, then once you have logged in click on the 
    Join Question link below.
    
    Join Question: http://%s
    """
    return send_email("Vilfredo - Invitation to participate",
                      app.config['ADMINS'][0],
                      recipient_email,
                      body_template % (sender.username, question.title, 
                                       app.config['SITE_DOMAIN'],
                                       app.config['SITE_DOMAIN']+'/invitation/'+token))

