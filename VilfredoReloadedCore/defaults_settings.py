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

# default configuration settings

# WARNNG: must be changed in production!

# Set proocol http:// or https://
PROTOCOL = 'http://'

# Set site domain
SITE_DOMAIN = '0.0.0.0:8080'

# Set static domain
CDN_DOMAIN = SITE_DOMAIN

# DATABASE_URI = 'sqlite:////var/tmp/vr.db'
development_db = 'sqlite:////var/tmp/vr.db'

CACHE_COMPLEX_DOM = True

# Set path to log file
LOG_FILE_PATH = '/var/tmp/vr.log'

# Set path to pickle work files
WORK_FILE_DIRECTORY = '/var/tmp/work'

# Set max upload file size 
MAX_CONTENT_LENGTH = 2 * 1024 * 1024

# If True people can only register if invited by email
REGISTER_INVITATION_ONLY = False

# Set path to uploaded user files
UPLOADED_FILES_DEST = 'static/usercontent/uploads'

USER_CONTENT = 'usercontent/uploads'

# Set path to uploaded user files
UPLOADED_AVATAR_DEST = 'static/usercontent/profiles'

PROFILE_PICS = 'usercontent/profiles'

# Set permitted extensions for uploaded user files
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']

# name of logger configuration file
LOG_CONFIG_FILE = 'logging_debug.conf'

# On some systems (Dreamhost, perhaps because they use Passenger) it is required to 
# manually set the path to the Graphviz dot executible, eg
# GRAPHVIZ_DOT_PATH = '/home/vilfredo/local/bin/dot'
GRAPHVIZ_DOT_PATH = None

# Directory to put the voting maps - it will be created if not found
# MAP_PATH = 'maps/'
MAP_PATH = 'VilfredoReloadedCore/static/maps/'
EXTERNAL_MAP_PATH = 'maps/'
# MAP_PATH = 'maps/'
# EXTERNAL_MAP_PATH = 'maps/'

# DATABASE_URI = development_db
SQLALCHEMY_DATABASE_URI = development_db

# WARNNG: must be changed to False in production!
DEBUG = True

# WARNNG: must be changed in production!
SECRET_KEY = 'ai4ohngaek4ohchaesheeY2Xee2jishe'
SALT = 'vilfredoiscool'

# mail server settings - ARNNG: must be changed to False in production!
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USERNAME = 'admin'
MAIL_PASSWORD = None
MAIL_SUPPRESS_SEND = True
MAIL_DEFAULT_SENDER = 'no_reply@localhost'

from datetime import timedelta
REMEMBER_COOKIE_DURATION = timedelta(days=365)

# administrator list
ADMINS = ['admin@' + SITE_DOMAIN]

ANONYMIZE_GRAPH = False

SEND_EMAIL_NOTIFICATIONS = True

ALGORITHM_VERSION = 2

QUESTION_PERMISSION_DENIED_MESSAGE = "You have not been invited to participate in this question"
QUESTION_VOTE_PERMISSION_DENIED_MESSAGE = "You have not been invited to vote in this question"
QUESTION_PROPOSE_PERMISSION_DENIED_MESSAGE = "You have not been invited to write in this question"

# API
RESULTS_PER_PAGE = 50
MAX_LEN_EMAIL = 120
MAX_LEN_USERNAME = 20
MAX_LEN_PASSWORD = 120
MIN_LEN_PASSWORD = 6
MAX_LEN_ROOM = 20
MIN_LEN_ROOM = 2
MAX_LEN_PROPOSAL_TITLE = 120
MAX_LEN_PROPOSAL_ABSTRACT = 5000
MAX_LEN_PROPOSAL_BLURB = 10000
MAX_LEN_QUESTION_TITLE = 120
MAX_LEN_QUESTION_BLURB = 10000
MAX_LEN_PROPOSAL_COMMENT = 1000
MAX_LEN_PROPOSAL_QUESTION = 1000
MAX_LEN_PROPOSAL_QUESTION_ANSWER = 1000
PWD_RESET_LIFETIME = 3600*24*2
EMAIL_VERIFY_LIFETIME = 3600*24*2