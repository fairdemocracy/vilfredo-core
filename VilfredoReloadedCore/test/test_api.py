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

from .. import app
from .. import api
from .. database import drop_db, init_db
import base64
import json
import os

DELETE_DB_ON_EXIT = False
MAKE_GRAPH = True


class RESTAPITestCase(unittest.TestCase):
    def setUp(self):
        # app.logger.debug("Create DB")
        # init_db()
        # For SQLite development DB only
        if 'vr.db' in app.config['SQLALCHEMY_DATABASE_URI']:
            # Drop existing DB first
            if os.path.isfile('/var/tmp/vr.db'):
                app.logger.debug("Dropping existing sqlite db\n")
                drop_db()
            # Create empty SQLite test DB
            app.logger.debug("Initializing sqlite db\n")
            init_db()

            app.config['TESTING'] = True
            self.app = app.test_client()
        else:
            app.logger.debug("Using historical db: skipping test %s.... ",
                             __name__)
            print "Using historical db: skipping test %s.... " % (__name__)

    def tearDown(self):
        # For SQLite development DB only
        if 'vr.db' in app.config['SQLALCHEMY_DATABASE_URI'] \
                and DELETE_DB_ON_EXIT:
            app.logger.debug("Dropping sqlite db\n")
            drop_db()

    def open_with_json_auth(self, url, method, data, username, password):
        return self.app.open(
            url,
            content_type='application/json',
            method=method,
            data=json.dumps(data),
            headers={'Authorization': 'Basic ' +
                     base64.b64encode(username + ":" + password)})

    def open_with_json(self, url, method, data):
        return self.app.open(url,
                             content_type='application/json',
                             method=method,
                             data=json.dumps(data))

    def open_with_auth(self, url, method, data, username, password):
        return self.app.open(
            url,
            method=method,
            headers={'Authorization': 'Basic ' +
                     base64.b64encode(username + ":" + password)})

    def get_message(self, rv):
        data = json.loads(rv.data)
        if 'message' in data:
            return data['message']
        else:
            return "No error message returned"

    def test_rest_api(self):
        #
        # Don't run against histroical data DB
        #
        if not 'vr.db' in app.config['SQLALCHEMY_DATABASE_URI']:
            return

        #
        # Create Users
        #
        # rv = self.app.post('/api/v1/users', data=payload,
        #                    content_type='application/json')
        rv = self.open_with_json('/api/v1/users',
                                 'POST',
                                 dict(username='john',
                                      email='john@example.com',
                                      password='test123'))
        # Log data received
        app.logger.debug("Data retrieved from Create User = %s\n", rv.data)
        self.assertEqual(rv.status_code, 201)
        data = json.loads(rv.data)
        app.logger.debug("New user at = %s\n", data['url'])

        # Attempt to create a user with a duplicate username
        rv = self.open_with_json('/api/v1/users',
                                 'POST',
                                 dict(username='john',
                                      email='john@example.com',
                                      password='test123'))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual('Username not available',
                         self.get_message(rv),
                         self.get_message(rv))
        app.logger.debug("Create user with duplicate username: Message: %s",
                         self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved from Create Duplicate User = %s\n",
                         rv.data)

        # Attempt to create a user with a duplicate email
        rv = self.open_with_json('/api/v1/users',
                                 'POST',
                                 dict(username='keith',
                                      email='john@example.com',
                                      password='test123'))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual('Email not available', self.get_message(rv),
                         self.get_message(rv))
        app.logger.debug(
            "Create user with duplicate email address: Message: %s",
            self.get_message(rv))
        # Log data received
        app.logger.debug(
            "Data retrieved from Create User/dupicate email = %s\n",
            rv.data)

        # Attempt to create a user with too short a password
        rv = self.open_with_json('/api/v1/users',
                                 'POST',
                                 dict(username='keith',
                                      email='keith@example.com',
                                      password='12345'))
        self.assertEqual(rv.status_code, 400)
        self.assertIn('Password must be between',
                      self.get_message(rv),
                      self.get_message(rv))
        app.logger.debug("Create user with too short a password: Message: %s",
                         self.get_message(rv))

        rv = self.open_with_json('/api/v1/users',
                                 'POST',
                                 dict(username='susan',
                                      email='susan@example.com',
                                      password='test123'))
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json('/api/v1/users',
                                 'POST',
                                 dict(username='bill',
                                      email='bill@example.com',
                                      password='test123'))
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json('/api/v1/users',
                                 'POST',
                                 dict(username='jack',
                                      email='jack@example.com',
                                      password='test123'))
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json('/api/v1/users',
                                 'POST',
                                 dict(username='harry',
                                      email='harry@example.com',
                                      password='test123'))
        self.assertEqual(rv.status_code, 201)

        #
        # Create Question
        #
        rv = self.open_with_json_auth('/api/v1/questions',
                                      'POST',
                                      dict(title='My question',
                                           blurb='My blurb',
                                           room='vilfredo',
                                           minimum_time=0),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 201)
        data = json.loads(rv.data)
        app.logger.debug("New question at = %s\n", data['url'])
        # Log data received
        app.logger.debug("Data retrieved from Create Question = %s\n",
                         rv.data)

        #
        # Create More Questions
        #
        rv = self.open_with_json_auth('/api/v1/questions',
                                      'POST',
                                      dict(title='Another Question',
                                           blurb='Blah blah Blah blah Blah',
                                           room='vilfredo',
                                           minimum_time=0),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth('/api/v1/questions',
                                      'POST',
                                      dict(title='Too Many Chefs',
                                           blurb='How to Spoil the broth?',
                                           room='vilfredo',
                                           minimum_time=0),
                                      'harry',
                                      'test123')
        self.assertEqual(rv.status_code, 201)

        #
        # Create Invites
        #
        rv = self.open_with_json_auth('/api/v1/questions/1/invitations',
                                      'POST',
                                      dict(invite_user_ids=[2, 3, 4, 5]),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 201)
        # Log data received
        app.logger.debug("Data retrieved from Create Invite = %s\n", rv.data)

        #
        # Get Invites
        #
        rv = self.open_with_json_auth('/api/v1/questions/1/invitations',
                                      'GET',
                                      dict(),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Invites = %s\n", rv.data)

        #
        # Create Subscriptions
        #
        rv = self.open_with_json_auth('/api/v1/users/1/subscriptions',
                                      'POST',
                                      dict(question_id=1, how='asap'),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 201)
        # Log data received
        app.logger.debug("Data retrieved from Create Subscription = %s\n",
                         rv.data)

        rv = self.open_with_json_auth('/api/v1/users/1/subscriptions',
                                      'POST',
                                      dict(question_id=2, how='asap'),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth('/api/v1/users/1/subscriptions',
                                      'POST',
                                      dict(question_id=3, how='weekly'),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth('/api/v1/users/5/subscriptions',
                                      'POST',
                                      dict(question_id=3, how='daily'),
                                      'harry',
                                      'test123')
        self.assertEqual(rv.status_code, 201)

        #
        # Update Subscriptions
        #
        rv = self.open_with_json_auth('/api/v1/users/5/subscriptions',
                                      'PATCH',
                                      dict(question_id=3, how='asap'),
                                      'harry',
                                      'test123')
        # Log data received
        app.logger.debug("Data retrieved from Update Subscriptions = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201)

        #
        # Get Subscriptions
        #
        rv = self.open_with_json_auth('/api/v1/users/1/subscriptions',
                                      'GET',
                                      dict(),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Subscriptions = %s\n",
                         rv.data)

        #
        # Get question subscribers
        #
        rv = self.open_with_json_auth('/api/v1/questions/3/subscribers',
                                      'GET',
                                      dict(),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Question Subscribers = %s\n",
                         rv.data)

        #
        # Delete Subscription
        #
        rv = self.open_with_json_auth('/api/v1/users/1/subscriptions/3',
                                      'DELETE',
                                      dict(),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Delete Subscription = %s\n",
                         rv.data)

        #
        # Create Proposals
        #
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals',
            'POST',
            dict(title='Bills First Proposal',
                 blurb='Bills blurb of varying interest'),
            'bill',
            'test123')
        self.assertEqual(rv.status_code, 201)
        # Log data received
        app.logger.debug("Data retrieved from Create Proposal = %s\n",
                         rv.data)

        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals',
            'POST',
            dict(title='Bills Second Proposal',
                 blurb='Bills blurb of varying disinterest',
                 abstract='This is too abstract for an abstract'),
            'bill',
            'test123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals',
            'POST',
            dict(title='Susans Only Proposal',
                 blurb='My blub is cool',
                 abstract='Blah blah blah'),
            'susan',
            'test123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals',
            'POST',
            dict(
                title='Harrys Cool Proposal',
                blurb='Harry wrties like a champ'),
            'harry',
            'test123')
        self.assertEqual(rv.status_code, 201)

        data = json.loads(rv.data)
        new_proposal_url = data['url']
        app.logger.debug("New propoal URL = %s", new_proposal_url)

        # Harry edits his proposal
        rv = self.open_with_json_auth(
            new_proposal_url,
            'PATCH',
            dict(
                title='Harrys Cooler Proposal',
                blurb='Harry edits like a champ'),
            'harry',
            'test123')
        self.assertEqual(rv.status_code, 200, self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved from Edit Proposal = %s\n",
                         rv.data)

        #
        # Get Question Proposals
        #
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals',
            'GET',
            dict(),
            'bill',
            'test123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Question Proposals = %s\n",
                         rv.data)

        #
        # Author attempts to Delete a Question - Disallowed
        # because it has proposals
        #
        rv = self.open_with_json_auth('/api/v1/questions/1',
                                      'DELETE',
                                      dict(),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 403, self.get_message(rv))
        self.assertIn("This question has proposals",
                      self.get_message(rv),
                      self.get_message(rv))
        app.logger.debug("Response message: %s", self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved = %s\n", rv.data)

        #
        # Author move question on
        #
        rv = self.open_with_json_auth('/api/v1/questions/1',
                                      'PATCH',
                                      dict(move_on=True),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 200, self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved from Edit Question (Move On) = %s\n",
                         rv.data)

        #
        # Create then Delete a Proposal.
        # Must be done in the writing phase where the proposal was created.
        #
        rv = self.open_with_json_auth(
            '/api/v1/questions/3/proposals',
            'POST',
            dict(
                title="My less than stirling proposal",
                blurb="This is not very good. Think I'll delete it."),
            'harry',
            'test123')
        app.logger.debug("Data retrieved from Create Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201)
        data = json.loads(rv.data)
        harrys_proposal_url = data['url']
        #
        # Delete the proposal
        #
        app.logger.debug("Harry deletes his proposal with url: %s",
                         harrys_proposal_url)
        rv = self.open_with_json_auth(
            harrys_proposal_url,
            'DELETE',
            dict(),
            'harry',
            'test123')
        app.logger.debug("Harry deletes his proposal - message: %s",
                         self.get_message(rv))
        app.logger.debug("Data retrieved from Delete Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 200)

        #
        # Create Endorsements
        #
        # susans_prop1.endorse(susan)
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/3/endorsements',
            'POST',
            dict(),
            'susan',
            'test123')
        self.assertEqual(rv.status_code, 201)
        # Log data received
        app.logger.debug("Data retrieved from Create Endorsement = %s\n",
                         rv.data)

        # susans_prop1.endorse(john)
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/3/endorsements',
            'POST',
            dict(),
            'john',
            'test123')
        self.assertEqual(rv.status_code, 201)

        #
        # Comments, oppose, confused
        #
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/4/endorsements',
            'POST',
            dict(
                endorsement_type="oppose",
                supported_comment_ids=[],
                new_comment_text="This is terrible!"),
            'john',
            'test123')
        app.logger.debug("Data retrieved from Oppose Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201, rv.status_code)

        # Add OPPOSED endorsement and comment
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/4/endorsements',
            'POST',
            dict(
                endorsement_type="oppose",
                new_comment_text="This is terrible!"),
            'harry',
            'test123')
        app.logger.debug("Data retrieved from Oppose Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201, rv.status_code)

        # Add CONFUSED endorsement and comment
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/4/endorsements',
            'POST',
            dict(
                endorsement_type="confused",
                supported_comment_ids=[1],
                new_comment_text="I feel very confused!"),
            'bill',
            'test123')
        app.logger.debug("Data retrieved from Confused by Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201, rv.status_code)

        #
        # Get comments
        #
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/4/comments',
            'GET',
            dict(),
            'john',
            'test123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Comments = %s\n", rv.data)

        # bills_prop1.endorse(john)
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/1/endorsements',
            'POST',
            dict(),
            'john',
            'test123')
        self.assertEqual(rv.status_code, 201)

        # bills_prop2.endorse(bill)
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/2/endorsements',
            'POST',
            dict(),
            'bill',
            'test123')
        self.assertEqual(rv.status_code, 201)

        # harrys_prop1.endorse(jack)
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/4/endorsements',
            'POST',
            dict(),
            'jack',
            'test123')
        self.assertEqual(rv.status_code, 201)

        # harrys_prop1.endorse(susan)
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/4/endorsements',
            'POST',
            dict(),
            'susan',
            'test123')
        self.assertEqual(rv.status_code, 201)

        # bills_prop1.endorse(harry)
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/1/endorsements',
            'POST',
            dict(),
            'harry',
            'test123')
        self.assertEqual(rv.status_code, 201)

        # susans_prop1.endorse(harry)
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/3/endorsements',
            'POST',
            dict(),
            'harry',
            'test123')
        self.assertEqual(rv.status_code, 201)

        #
        # Get Proposal Endorsers
        #
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/3/endorsers',
            'GET',
            dict(),
            'harry',
            'test123')
        self.assertEqual(rv.status_code, 200, rv.status_code)
        app.logger.debug("Data retrieved = %s\n", rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Get Proposal Endorsers = %s\n",
                         rv.data)

        #
        # Get Question Pareto
        #
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/pareto',
            'GET',
            dict(),
            'harry',
            'test123')
        self.assertEqual(rv.status_code, 200, rv.status_code)
        app.logger.debug("Data retrieved = %s\n", rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Get Question Pareto = %s\n",
                         rv.data)

        #
        # Get Key Players
        #
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/key_players',
            'GET',
            dict(),
            'harry',
            'test123')
        self.assertEqual(rv.status_code, 200, rv.status_code)
        app.logger.debug("Data retrieved = %s\n", rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Get Key Players = %s\n",
                         rv.data)

        #
        # Get Endorser Effects
        #
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/endorser_effects',
            'GET',
            dict(),
            'harry',
            'test123')
        self.assertEqual(rv.status_code, 200, rv.status_code)
        app.logger.debug("Endorser Effects data retrieved = %s\n", rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Get Endorser Effects= %s\n",
                         rv.data)

        #
        # Get Proposal Relations
        #
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposal_relations',
            'GET',
            dict(),
            'harry',
            'test123')
        self.assertEqual(rv.status_code, 200, rv.status_code)
        # Log data received
        app.logger.debug("Data retrieved from Get Proposal Relations = %s\n",
                         rv.data)

        if (MAKE_GRAPH):
            #
            # Create Voting Map
            #
            rv = self.open_with_json_auth(
                '/api/v1/questions/1/graph?generation=1&map_type=all',
                'GET',
                dict(),
                'harry',
                'test123')
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            app.logger.debug("Data retrieved from get graph = %s\n", data)
            self.assertIn('map_Q1_G1_all_1_1.svg', data['url'],
                          "File URL not returned")

        #
        # Update Endorsements
        #
        # John ID=1 endorses proposal 2
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/2/endorsements',
            'POST',
            dict(),
            'john',
            'test123')
        self.assertEqual(rv.status_code, 201)
        #
        # Updates endorsement to OPPOSE
        app.logger.debug("John updates his endopsement to OPPOSE")
        rv = self.open_with_json_auth(
            '/api/v1/questions/1/proposals/2/endorsements',
            'PATCH',
            dict(endorsement_type='oppose'),
            'john',
            'test123')
        self.assertEqual(rv.status_code, 200, self.get_message(rv))
        self.assertEqual("Endorsement updated",
                         self.get_message(rv),
                         self.get_message(rv))
        app.logger.debug("Response message: %s", self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved from Update Endorsement = %s\n",
                         rv.data)

        #
        # Create Another Question
        #
        rv = self.open_with_json_auth('/api/v1/questions',
                                      'POST',
                                      dict(title='My boring question',
                                           blurb='My boring blurb',
                                           room='test',
                                           minimum_time=0),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 201)
        data = json.loads(rv.data)
        app.logger.debug("New question at = %s\n", data['url'])
        new_question_url = data['url']

        #
        # Author Deletes Question
        #
        rv = self.open_with_json_auth(new_question_url,
                                      'DELETE',
                                      dict(),
                                      'john',
                                      'test123')
        self.assertEqual(rv.status_code, 200, self.get_message(rv))
        self.assertIn("Question deleted",
                      self.get_message(rv),
                      self.get_message(rv))
        app.logger.debug("Response message: %s", self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved from Delete Question = %s\n",
                         rv.data)

    def get_questions(self):
        rv = self.app.get('/api/v1/users')
        #  rv = self.open_with_auth(
        #    '/api/v1/users', 'GET', None, 'grippo', 'test123')
        app.logger.debug("Data retrieved = %s\n", rv.data)
        self.assertEqual(rv.status_code, 200)

        rv = self.open_with_auth('/api/v1/users/50', 'GET',
                                 None, 'grippo', 'test123')
        app.logger.debug("Data retrieved = %s\n", rv.data)

        data = json.loads(rv.data)
        self.assertNotIn('email', data['object'])

        rv = self.open_with_auth('/api/v1/users/638', 'GET',
                                 None, 'grippo', 'test123')
        app.logger.debug("Data retrieved = %s\n", rv.data)

        data = json.loads(rv.data)
        app.logger.debug("Email retrieved = %s\n", data['object']['email'])
        self.assertIn('email', data['object'])

    def empty_db(self):
        """Start with a blank database."""
        rv = self.app.get('/')
        self.assertTrue('no questions' in rv.data, rv.data)
