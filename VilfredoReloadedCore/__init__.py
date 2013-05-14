# -*- coding: utf-8 -*-
#
# This file is part of VilfredoReloadedCore.
#
# Copyright (c) 2013 Daniele Pizzolli <daniele@ahref.eu>
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

:copyright: (c) 2013 by Daniele Pizzolli
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
"""

import pkg_resources
pkg_resources.declare_namespace(__name__)


from flask import Flask

from flask.ext.mail import Mail


def config_app(app):
    # Load setting using various methods
    # TODO: do relative o package import
    app.config.from_object('VilfredoReloadedCore.defaults_settings')
    # TODO: document the VCR_VARIABLE
    app.config.from_envvar('VRC_SETTINGS', silent=True)

    from .database import init_engine
    init_engine(app.config['DATABASE_URI'])

app = Flask(__name__)
config_app(app)
mail = Mail(app)
