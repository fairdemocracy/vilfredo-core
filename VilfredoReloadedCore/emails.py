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

def send_email(subject, sender_email, recipient_email, text_body):
    msg = MIMEText(text_body)
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    p = Popen(["/usr/sbin/sendmail", "-t"], stdin=PIPE)
    p.communicate(msg.as_string())
    # app.logger.debug("Return Code from email subprocess = %s", p.returncode)
    return p.returncode

def send_question_email_invite_email(sender, recipient_email, question, token):
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

def send_question_invite_email(sender, recipient, question):
    # print "Sending email:", sender.username, question.title
    body_template = \
    """
    Hi %s, Vilfredo user %s has invited you to participate in the question "%s".
    """
    return send_email("Vilfredo - Invitation to participate",
                      'admin@vilfredo.org',
                      recipient,
                      body_template % (recipient.username, sender.username, question.title))
