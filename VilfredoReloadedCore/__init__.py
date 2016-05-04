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

.. automodule:: VilfredoReloadedCore.api.v2.api
  :members:
"""

import pkg_resources
pkg_resources.declare_namespace(__name__)

import os, sys

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
from flask.ext.cdn import CDN


def config_app(app):
    # Load settings (summing defaults and custom config)
    # TODO: We should do a relative or package import
    app.config.from_object('VilfredoReloadedCore.defaults_settings')
    config = os.path.join(app.root_path, 'settings.cfg')
    if os.path.isfile(config):
        app.config.from_pyfile(config)
        app.logger.info("Loading config file: "+config)
    elif 'VILFREDO_SETTINGS' in os.environ:
      config = os.path.join(os.environ['VILFREDO_SETTINGS'], 'settings.cfg')
      if os.path.isfile(config):
          app.config.from_pyfile(config)
          app.logger.info("Loading config file: "+os.path.join(os.environ['VILFREDO_SETTINGS'], 'settings.cfg'))
      else:
          app.logger.warning('Failed to load configuration file from VILFREDO_SETTINGS: %s', config)


app = Flask(__name__, static_url_path='')
config_app(app)

import VilfredoReloadedCore.views
import VilfredoReloadedCore.api.v2.api

mail = Mail(app)

CDN(app)

if not os.path.exists(app.config['WORK_FILE_DIRECTORY']):
    try:
        app.logger.info('Creating work directory %s', app.config['WORK_FILE_DIRECTORY'])
        os.makedirs(app.config['WORK_FILE_DIRECTORY'])
    except IOError:
        raise sys.exit('Failed to create work directory %s. Please create it manually and restart the app.', app.config['WORK_FILE_DIRECTORY'])

if not os.path.exists(app.config['PROFILE_LOG_PATH']):
    try:
        os.makedirs(app.config['PROFILE_LOG_PATH'])
    except IOError:
        raise sys.exit('Failed to create profile log directory %s', app.config['PROFILE_LOG_PATH'])


if app.config['PROFILE']:
    from werkzeug.contrib.profiler import ProfilerMiddleware
    # ProfilerMiddleware(app, stream=None, sort_by=('cumulative', 'time', 'calls'), restrictions=(), profile_dir=None)
    if app.config['PROFILE_LOG']:
      try:
          log_file_path = os.path.join(app.config['PROFILE_LOG_PATH'], app.config['PROFILE_LOG'])
          profile_log = open(log_file_path, "a")
          app.wsgi_app = ProfilerMiddleware(app.wsgi_app, sort_by=('time', 'calls'), stream=profile_log, restrictions=[30])
      except IOError:
          raise sys.exit('Failed to create profile log file %s', app.config['PROFILE_LOG'])
    else:
      app.wsgi_app = ProfilerMiddleware(app.wsgi_app, sort_by=('time', 'calls'), restrictions=[30])


from flask_util_js import FlaskUtilJs
fujs = FlaskUtilJs(app)

# Logging
import logging
import logging.config
basedir = os.path.abspath(os.path.dirname(__file__))
# config_file = os.path.join(basedir, app.config['LOG_CONFIG_FILE'])

# Check if environment variable VILFREDO_SETTINGS is set
if 'VILFREDO_SETTINGS' in os.environ\
        and os.path.isfile(os.path.join(os.environ['VILFREDO_SETTINGS'], app.config['LOG_CONFIG_FILE'])):
    config_file = os.path.join(os.environ['VILFREDO_SETTINGS'], app.config['LOG_CONFIG_FILE'])
else:
    config_file = os.path.join(basedir, app.config['LOG_CONFIG_FILE'])
logging.config.fileConfig(config_file)
logger = logging.getLogger('vilfredo_logger')
logger.propagate = False

# Apply the logger.handlers to the flask application
for lh in logger.handlers:
    app.logger.addHandler(lh)