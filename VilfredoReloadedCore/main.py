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
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with VilfredoReloadedCore.  If not, see
# <http://www.gnu.org/licenses/>.
#
###############################################################################

'''
Main
====

Convenience module to run vilfredo-reloaded-core
'''

from . import app
from . import api  # NOQA
from . import views


def main():
    '''Run vilfredo using built-in webserver on port 8080'''
    app.run(host='0.0.0.0', port=8080)
