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
from . import app
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# Login_serializer used to encryt and decrypt the cookie token for the remember
# me option of flask-login
from itsdangerous import URLSafeTimedSerializer
try:
    login_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], app.config['SALT'])
except Exception:
    print 'Failed to create login_serializer'