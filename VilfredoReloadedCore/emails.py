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

def email_question_email_invite(sender, recipient_email, question):
    # print "Sending email:", sender.username, question.title
    send_email("Vilfredo - Invitation to participate",
               'admin@vilfredo.org',
               recipient_email,
               "User %s invites you to participate in question %s"
               % (sender.username, question.title))

def email_question_invite(sender, recipient, question):
    # print "Sending email:", sender.username, question.title
    send_email("Vilfredo - Invitation to participate",
               'admin@vilfredo.org',
               recipient,
               "User %s invites you to participate in question %s"
               % (sender.username, question.title))
