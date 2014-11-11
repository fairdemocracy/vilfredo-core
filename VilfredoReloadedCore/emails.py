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

from flask_mail import Message

from . import app, mail

from decorators import async


@async
def send_async_email(msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(msg)


def email_question_email_invite(sender, receiver_email, question):
    # print "Sending email:", sender.username, question.title
    send_email("Vilfredo - Invitation to participate",
               'admin@vilfredo.org',
               [receiver_email],
               "User %s invites you to participate in question %s"
               % (sender.username, question.title),
               "User %s invites you to participate in question %s"
               % (sender.username, question.title))

def email_question_invite(sender, receiver, question):
    # print "Sending email:", sender.username, question.title
    send_email("Vilfredo - Invitation to participate",
               'admin@vilfredo.org',
               [receiver.email],
               "User %s invites you to participate in question %s"
               % (sender.username, question.title),
               "User %s invites you to participate in question %s"
               % (sender.username, question.title))
