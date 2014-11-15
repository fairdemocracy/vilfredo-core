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

# Set site domain
SITE_DOMAIN = '0.0.0.0:8080'

# DATABASE_URI = 'sqlite:////var/tmp/vr.db'
development_db = 'sqlite:////var/tmp/vr.db'

ALGORITHM_VERSION = 1

CACHE_COMPLEX_DOM = True

# Set path to log file
LOG_FILE_PATH = '/var/tmp/vr.log'

# name of logger configuration file
LOG_CONFIG_FILE = 'logging_debug.conf'

# On some systems (Dreamhost, perhaps because they use Passenger) it is required to 
# manually set the path to the Graphviz dot executible, eg
# GRAPHVIZ_DOT_PATH = '/home/vilfredo/local/bin/dot'
GRAPHVIZ_DOT_PATH = None

# Directory to put the voting maps - it will be created if not found
# MAP_PATH = 'maps/'
MAP_PATH = 'VilfredoReloadedCore/static/maps/'
EXTERNAL_MAP_PATH = 'static/maps/'
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