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


"""
Vilfredo Reloaded Core
======================

:copyright: © 2009-2013 Pietro Speroni di Fenizio & Derek Paterson
:license: AGPL 3, see LICENSE.txt for more details


Module documentation
--------------------

.. automodule:: VilfredoReloadedCore.defaults_settings
  :members:

.. automodule:: VilfredoReloadedCore.database
  :members:

.. automodule:: VilfredoReloadedCore.models
  :members:

.. automodule:: VilfredoReloadedCore.views
  :members:

.. automodule:: VilfredoReloadedCore.main
  :members:

.. automodule:: VilfredoReloadedCore.api
  :members:
"""

import pkg_resources
pkg_resources.declare_namespace(__name__)


# The __init__.py must contain the app
# http://flask.pocoo.org/docs/patterns/packages/
# but the __init__.py is run by setup.py
# http://stackoverflow.com/questions/12383246/why-does-setup-py-runs-the-package-init-py # NOQA
# so, this is a workaround to handle both
try:
    from flask import Flask
except ImportError:
    import sys
    sys.exit("You should not reach this point")

from flask.ext.mail import Mail


def config_app(app):
    # Load setting using various methods
    # TODO: do relative o package import
    app.config.from_object('VilfredoReloadedCore.defaults_settings')
    # TODO: document the VCR_VARIABLE
    app.config.from_envvar('VRC_SETTINGS', silent=True)

    # from .database import init_engine
    # init_engine(app.config['DATABASE_URI'])

app = Flask(__name__)
config_app(app)

#from flask.ext.sqlalchemy import SQLAlchemy
#db = SQLAlchemy(app)

import VilfredoReloadedCore.views
import VilfredoReloadedCore.api

mail = Mail(app)

from flask_util_js import FlaskUtilJs
fujs = FlaskUtilJs(app)

# Logging
import logging
import logging.config

# Set logging
import os
basedir = os.path.abspath(os.path.dirname(__file__))
config_file = os.path.join(basedir, app.config['LOG_CONFIG_FILE'])

# Passing mode='w' to file handler not causing overwrite
if os.path.isfile('/var/tmp/vr.log'):
    try:
        os.remove('/var/tmp/vr.log')
    except IOError:
        print 'Failed to delete log file /var/tmp/vr.log'


logging.config.fileConfig(config_file)
# create logger
logger = logging.getLogger('vilfredo_logger')
logger.propagate = False

# Apply the logger.handlers to the flask application
for lh in logger.handlers:
    app.logger.addHandler(lh)

# from flask_login import LoginManager
# login_manager = LoginManager()
# login_manager.init_app(app)

# Login_serializer used to encryt and decrypt the cookie token for the remember
# me option of flask-login

# from itsdangerous import URLSafeTimedSerializer
# try:
#     login_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], app.config['SALT'])
# except Exception:
#     print 'Failed to create login_serializer'
