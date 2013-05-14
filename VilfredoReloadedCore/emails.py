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
Emails
'''

from flask_mail import Message

from . import app, mail

from decorators import async

#
#import smtplib

# Import the email modules we'll need
#from email.mime.text import MIMEText


@async
def send_async_email(msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(msg)
    """
    mail.send_message(subject=subject,
                      body=text_body,
                      recipients=recipients)
    """


def email_question_invite(sender, receiver, question):
    print "Sending email:", sender.username, question.title
    send_email("Vilfredo Reloaded - Invitation to participate",
               'admin@vilfredo-reloaded.com',
               [receiver.email],
               "User %s invites you to participate in question %s"
               % (sender.username, question.title),
               "User %s invites you to participate in question %s"
               % (sender.username, question.title))
