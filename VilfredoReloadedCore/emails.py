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

def send_added_to_question_email(inviter, receiver, question):
    '''
    .. function:: send_email_verification(email, token)

    Send an email to notify someone that they have been added to a question.

    :param inviter: participant granting access to a question
    :type user: User
    :param receiver: invited participant
    :type user: User
    :param question: question
    :type toquestionken: Question
    :rtype: long
    '''
    body_template = \
    """
    User %s has added you to the question %s.
    
    %s%s/question/%s
    """
    return send_email("Vilfredo - Please Participate",
                      app.config['ADMINS'][0],
                      receiver.email,
                      body_template % (inviter.username,
                                       question.title,
                                       app.config['PROTOCOL'],
                                       app.config['SITE_DOMAIN'],
                                       question.id))

def send_user_already_added_email(user, email, question):
    '''
    .. function:: send_email_verification(email, token)

    Send an email to notify someone has already accepted an invitation.

    :param user: question participant
    :type user: User
    :param question: question
    :type toquestionken: Question
    :rtype: long
    '''
    body_template = \
    """
    The invitation you sent to %s for question "%s" appears to belong to a user who has already accepted an earlier invitation for that question.
    
    %s%s/question/%s
    """
    return send_email("Vilfredo - Email Invitation Update",
                      app.config['ADMINS'][0],
                      user.email,
                      body_template % (email, 
                                       question.title, 
                                       app.config['PROTOCOL'],
                                       app.config['SITE_DOMAIN'], 
                                       question.id))

def send_email_invite_accepted_email(user, email, question):
    '''
    .. function:: send_email_verification(email, token)

    Send an email to notify someone has accepted an invitation.

    :param user: question participant
    :type user: User
    :param question: question
    :type toquestionken: Question
    :rtype: long
    '''
    app.logger.debug('send_email_invite_accepted_email called...')
    body_template = \
    """
    The invitation you sent to %s for question "%s" has been accepted.
    
    %s%s/question/%s
    """
    return send_email("Vilfredo - Invitation Accepted",
                      app.config['ADMINS'][0],
                      user.email,
                      body_template % (email, 
                                       question.title,
                                       app.config['PROTOCOL'],
                                       app.config['SITE_DOMAIN'], 
                                       question.id))

def send_welcome_to_notfound_question_email(user, question_id):
    '''
    .. function:: send_welcome_email(user, question_id)

    Send an email to welcome the new user who received an email invitation.

    :param user: question participant
    :type user: User
    :param question: question
    :type toquestionken: Question
    :rtype: long
    '''
    app.logger.debug('send_welcome_to_notfound_question_email called...')
    body_template = \
    """
    Hi %s! Welcome to Vilfredo! Thanks for joining us!
    
    You had agreed to participate in %s's question "%s" but unfortunately it appears to no longer exist. Sorry about that.
    
    You can of course start your own question and invite others to participate.
    """
    return send_email("Welcome to Vilfredo!",
                      app.config['ADMINS'][0],
                      user.email,
                      body_template % (user.username,
                                       question.author.username,
                                       question.title,
                                       app.config['SITE_DOMAIN'],
                                       question.id))

def send_welcome_to_question_email(user, question):
    '''
    .. function:: send_welcome_to_question_email(user, question)

    Send an email to welcome the new user who received an email invitation.

    :param user: question participant
    :type user: User
    :param question: question
    :type toquestionken: Question
    :rtype: long
    '''
    app.logger.debug('send_welcome_to_question_email called...')
    body_template = \
    """
    Hi %s! Welcome to Vilfredo! Thanks for joining us!

    You have agreed to participate in %s's question "%s". You can find it at the link below or by logging in and looking under your active questions.
    
    %s%s/question/%s
    """
    return send_email("Welcom to Vilfredo!",
                      app.config['ADMINS'][0],
                      user.email,
                      body_template % (user.username,
                                       question.author.username,
                                       question.title,
                                       app.config['PROTOCOL'],
                                       app.config['SITE_DOMAIN'],
                                       question.id))


def send_moved_on_email(user, question):
    '''
    .. function:: send_email_verification(email, token)

    Send an email to notify that a question has moved on to a new stage.

    :param user: question participant
    :type user: User
    :param question: question
    :type toquestionken: Question
    :rtype: long
    '''
    body_template = \
    """
    The question titled "%s" has now moved on to the %s stage.
    
    %s%s/question/%s
    """
    return send_email("Vilfredo - Question %s Now %s" % (question.title, question.phase),
                      app.config['ADMINS'][0],
                      user.email,
                      body_template % (question.title,
                                       question.phase,
                                       app.config['PROTOCOL'],
                                       app.config['SITE_DOMAIN'],
                                       question.id))

def send_email_verification(user_id, email, token):
    '''
    .. function:: send_email_verification(email, token)

    Send an email containing a link to allow someone to activate their account.

    :param email: user email address
    :type email: string
    :param token: verification token
    :type token: string
    :rtype: long
    '''
    body_template = \
    """
    Welcome to Vilfredo! Great to have you with us!
    
    Click on the link below to activate your account.
    
    Activate Account: %s%s
    """
    return send_email("Vilfredo - Activate Your Account",
                      app.config['ADMINS'][0],
                      email,
                      body_template % (app.config['PROTOCOL'],
                                       app.config['SITE_DOMAIN']+'/activate'+'?u='+str(user_id)+'&t='+token))

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
    
    Reset Password: %s%s
    """
    return send_email("Vilfredo - Password Reset Request",
                      app.config['ADMINS'][0],
                      email,
                      body_template % (app.config['PROTOCOL'],
                                       app.config['SITE_DOMAIN']+'/resetpwd/'+token))

def send_question_email_invite_email(sender, recipient_email, question, token):
    '''
    .. function:: send_question_email_invite_email(sender, recipient_email, question, token)

    Send an email containing a link to invite someone to participate in a question.

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
    app.logger.debug('send_question_email_invite_email called...')
    body_template = \
    """
    Hi!
    
    %s invites you to participate in the question "%s" on Vilfredo.
    
    If you wish to participate please click on the link below and follow the instructions.
    
    Click to participate: %s%s
    """
    return send_email("Vilfredo - Invitation to participate",
                      app.config['ADMINS'][0],
                      recipient_email,
                      body_template % (sender.username,
                                       question.title,
                                       app.config['PROTOCOL'],
                                       app.config['SITE_DOMAIN']+'/invitation'+'?eit='+token))

