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

'''
Database Models test for VilfredoReloadedCore
'''

# unittest2 offers TestCase.assertMultiLineEqual that provide a nice
# diff output, sometimes it is called automagically by the old
# assertEqual

try:
    import unittest2 as unittest
except ImportError:
    # NOQA
    import unittest

from .. import models
from .. database import db_session, drop_db, init_db


class ModelTest(unittest.TestCase):
    '''
    Model test
    '''

    def setUp(self):
        init_db()
        pass

    def tearDown(self):
        drop_db()

    def test_user_model(self):
        """Test user model"""

        user = models.LoginUser('test_username', 'test_email', 'test_password')
        db_session.add(user)
        db_session.commit()
        user1 = models.LoginUser.query.filter(
            models.LoginUser.username == 'test_username'
        ).first()
        self.assertEqual(user.email, user1.email)
