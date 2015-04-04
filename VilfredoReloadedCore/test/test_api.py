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
# from .. import api
from VilfredoReloadedCore.api.v2 import api
from VilfredoReloadedCore import models
from .. database import drop_db, init_db, db_session
import base64
import json
import os

DELETE_DB_ON_EXIT = False
DELETE_DB_ON_START = True
MAKE_GRAPH = True
MOVE_TO_GENERATION_2 = False
USE_VOTEMAP = True
CREATE_CONSENSUS = False
ALGORITHM_VERSION = "2"
SEND_EMAILS = False
os.environ["EMAIL_VALIDATION_OFF"] = '1'
os.environ["EMAIL_OFF"] = '1'


class RESTAPITestCase(unittest.TestCase):
    def setUp(self):
        # app.logger.debug("Create DB")
        # init_db()
        app.logger.debug('Running tests on database %s', app.config['SQLALCHEMY_DATABASE_URI'])
        # For SQLite development DB only
        if 'vr.db' in app.config['SQLALCHEMY_DATABASE_URI']:
            # Drop existing DB first
            if os.path.isfile('/var/tmp/vr.db') and DELETE_DB_ON_START:
                app.logger.debug("Dropping existing sqlite db\n")
                drop_db()
            # Create empty SQLite test DB
            app.logger.debug("Initializing sqlite db\n")
            init_db()
            app.config['TESTING'] = True
            self.app = app.test_client()
        else:
            if DELETE_DB_ON_START:
                app.logger.debug("Dropping existing DB\n")
                drop_db()
            app.logger.debug("Initializing DB\n")
            init_db()
            app.config['TESTING'] = True
            self.app = app.test_client()
            # Populate QuestionTypes
            db_session.add_all([models.QuestionTypes('standard'),
                                models.QuestionTypes('image')])
            db_session.commit()

    def tearDown(self):
        # For SQLite development DB only
        if 'vr.db' in app.config['SQLALCHEMY_DATABASE_URI'] and DELETE_DB_ON_EXIT:
            app.logger.debug("Dropping sqlite db\n")
            drop_db()
        elif DELETE_DB_ON_EXIT:
            app.logger.debug("Dropping DB\n")
            drop_db()

    def open_with_json_auth(self, url, method, data, username, password):
        return self.app.open(
            url,
            content_type='application/json',
            method=method,
            data=json.dumps(data),
            headers={'Authorization': 'Basic ' +
                     base64.b64encode(username + ":" + password)})

    def open_with_json_authtoken(self, url, method, data, authtoken):
        return self.app.open(
            url,
            content_type='application/json',
            method=method,
            data=json.dumps(data),
            headers={'Authorization': 'access_token:' + authtoken})

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

    def get_key_value(self, rv, key):
        data = json.loads(rv.data)
        if key in data:
            return data[key]
        else:
            return None

    def get_token(self, rv):
        data = json.loads(rv.data)
        app.logger.debug("data => %s", data)
        if 'token' in data['objects']:
            return data['objects']['token']
        else:
            return None

    def get_authtoken(self):
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/authtoken',
                                      'GET',
                                      dict(),
                                      'john',
                                      'john123')
        # Log data received
        app.logger.debug("Data retrieved from get Auth Token = %s\n", rv.data)
        token = self.get_token(rv)
        app.logger.debug("Auth Token = %s\n", token)

        if token:
            # Now authorize with token
            #
            # Create A Question using token to authenticate
            #
            rv = self.open_with_json_authtoken(api.REST_URL_PREFIX + '/questions',
                                     'POST',
                                      dict(title='My Token Question',
                                           blurb='My token blurb written while under the influence of an authentication token.',
                                           room='test'),
                                           token)
            self.assertEqual(rv.status_code, 201)
            data = json.loads(rv.data)
            app.logger.debug("New question at = %s\n", data['question']['url'])
            new_question_url = data['question']['url']
        else:
            app.logger.debug('No token returned')

        #
        # Get Question
        #
        # question_url = data['url']
        question_url = api.REST_URL_PREFIX + '/questions/1'
        rv = self.open_with_json_auth(question_url,
                                      'GET',
                                      dict(),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Get Question = %s\n",
                         rv.data)

    def test_rest_api(self):
        #
        # Create Users
        #
        # rv = self.app.post(api.REST_URL_PREFIX + '/users', data=payload,
        #                    content_type='application/json')
        rv = self.open_with_json(api.REST_URL_PREFIX + '/users',
                                 'POST',
                                 dict(username='john',
                                      email='john@example.com',
                                      password='john123'))
        # Log data received
        app.logger.debug("Data retrieved from Create User = %s\n", rv.data)
        self.assertEqual(rv.status_code, 201)
        data = json.loads(rv.data)
        app.logger.debug("New user at = %s\n", data['url'])

        rv = self.open_with_json(api.REST_URL_PREFIX + '/request_password_reset',
                                 'POST',
                                 dict(email='john@example.com'))
        # Log data received
        app.logger.debug("Data retrieved from Request Password Reset = %s\n", rv.data)
        self.assertEqual(rv.status_code, 201)

        # Attempt to create a user with a duplicate username
        rv = self.open_with_json(api.REST_URL_PREFIX + '/users',
                                 'POST',
                                 dict(username='john',
                                      email='john@example.com',
                                      password='john123'))
        self.assertEqual(rv.status_code, 400)
        # self.assertEqual('Username not available',
        #                  self.get_message(rv),
        #                  self.get_message(rv))
        app.logger.debug("Create user with duplicate username: Message: %s",
                         self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved from Create Duplicate User = %s\n",
                         rv.data)

        # Attempt to create a user with a duplicate email
        rv = self.open_with_json(api.REST_URL_PREFIX + '/users',
                                 'POST',
                                 dict(username='keith',
                                      email='john@example.com',
                                      password='john123'))
        self.assertEqual(rv.status_code, 400)
        # self.assertEqual('Email not available', self.get_message(rv),
        #                  self.get_message(rv))
        app.logger.debug(
            "Create user with duplicate email address: Message: %s",
            self.get_message(rv))
        # Log data received
        app.logger.debug(
            "Data retrieved from Create User/dupicate email = %s\n",
            rv.data)

        # Attempt to create a user with too short a password
        rv = self.open_with_json(api.REST_URL_PREFIX + '/users',
                                 'POST',
                                 dict(username='keith',
                                      email='keith@example.com',
                                      password='12345'))
        self.assertEqual(rv.status_code, 400)
        # self.assertIn('Password must be between',
        #               self.get_message(rv),
        #              self.get_message(rv))
        app.logger.debug("Create user with too short a password: Message: %s",
                         self.get_message(rv))

        rv = self.open_with_json(api.REST_URL_PREFIX + '/users',
                                 'POST',
                                 dict(username='susan',
                                      email='susan@example.com',
                                      password='susan123'))
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json(api.REST_URL_PREFIX + '/users',
                                 'POST',
                                 dict(username='bill',
                                      email='bill@example.com',
                                      password='bill123'))
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json(api.REST_URL_PREFIX + '/users',
                                 'POST',
                                 dict(username='jack',
                                      email='jack@example.com',
                                      password='jack123'))
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json(api.REST_URL_PREFIX + '/users',
                                 'POST',
                                 dict(username='harry',
                                      email='harry@example.com',
                                      password='harry123'))
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json(api.REST_URL_PREFIX + '/users',
                                 'POST',
                                 dict(username='tim',
                                      email='tim@example.com',
                                      password='tim123'))

        #
        # Create Question
        #
        blurb = """Right now there is no limit to the size of the answer that users can write. On the one side this is good, as it permit to users to spell out their idea in details, on the other it is a problem, as some users tend to write very long essays, making the partecipation difficult for everybody.<br>
<br>
From a certain point of view the problem is not massive, the more an answer is long the more people that do not understand it might not vote for it, generating a <i>de facto</i>, intrinsic push toward shorter answers.<br>
<br>
Yet many people feel a sense of duty to read all answers, and when confronted with too long answers they might simply pospone their voting process. With the result that they risk to fall out from the discussion cycle.<br>
<br>
What limit, if any, there should be to the length of the answer that the users are allowed to write?<br>
And how should this limit be imposed?<br>
Should this limit be decided once and for all, or should each person that asks the question decides the limit for that question?<br>
If this is the case, should the questioner be allowed to change this limit later in time?<br>
<br>
Sometimes it is possible to impose intrinsic limits, like the one said above. For example making the edit box smaller. And others are possible as well. If you have an idea about a soft limit that we could install, please share that too."""

        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions',
                                      'POST',
                                      dict(title='Wall of Text',
                                           blurb=blurb,
                                           room=''),
                                      'john',
                                      'john123')
        data = json.loads(rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Create Question = %s\n",
                         rv.data)
        app.logger.debug("New question at = %s\n", data['question']['url'])
        self.assertEqual(rv.status_code, 201)

        #
        # Get Question
        #
        question_url = data['question']['url']
        # question_url = api.REST_URL_PREFIX + '/questions/1'
        rv = self.open_with_json_auth(question_url,
                                      'GET',
                                      dict(),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Get Question = %s\n",
                         rv.data)

        #
        # Create More Questions
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions',
                                      'POST',
                                      dict(title='Another Question',
                                           blurb='Blah blah Blah blah Blah',
                                           room=''),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions',
                                      'POST',
                                      dict(title='Too Many Chefs',
                                           blurb='How to Spoil the broth?',
                                           room=''),
                                      'harry',
                                      'harry123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions',
                                      'POST',
                                      dict(title='Test Question',
                                           blurb='Should we run tests to make sure the system works?',
                                           room='test'),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 201)

        #
        # Create Invites
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions/1/invitations',
                                      'POST',
                                      dict(invite_user_ids=[2, 3, 4, 5, 6], permissions=7),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 201)
        # Log data received
        app.logger.debug("Data retrieved from Create Invite = %s\n", rv.data)

        #
        # Get Invites
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions/1/new_invites',
                                      'GET',
                                      dict(),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get New Invites = %s\n", rv.data)

        #
        # Accept Invites
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/2/new_invites/1/accept',
                                      'POST',
                                      dict(),
                                      'susan',
                                      'susan123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Invites = %s\n", rv.data)

        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/3/new_invites/2/accept',
                                      'POST',
                                      dict(),
                                      'bill',
                                      'bill123')
        self.assertEqual(rv.status_code, 200)

        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/4/new_invites/3/accept',
                                      'POST',
                                      dict(),
                                      'jack',
                                      'jack123')
        self.assertEqual(rv.status_code, 200)

        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/5/new_invites/4/accept',
                                      'POST',
                                      dict(),
                                      'harry',
                                      'harry123')
        self.assertEqual(rv.status_code, 200)

        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/6/new_invites/5/accept',
                                      'POST',
                                      dict(),
                                      'tim',
                                      'tim123')
        self.assertEqual(rv.status_code, 200)
        
        #
        # Fetch accepted invitations
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions/1/invitations',
                                      'GET',
                                      dict(),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Invites = %s\n", rv.data)

        #
        # Create Email Invites
        #
        user_emails = 'jenny@test.com,bademail.com,procrastinator@test.com'
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions/1/emailinvitations',
                                      'POST',
                                      dict(user_emails=user_emails, permissions=7),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 201)
        # Log data received
        app.logger.debug("Data retrieved from Create Invite = %s\n", rv.data)
        # self.assertEqual(rv.data.invites.rejected, 'bademail.com')
        # self.assertEqual(rv.data.invites.num_invites_sent, '2')
        if SEND_EMAILS:
            # Email invited users
            with mail.record_messages() as outbox:
                emails.email_question_invite(john, susan, johns_q)
                emails.email_question_invite(john, bill, johns_q)
                self.assertEqual(len(outbox), 2)
        '''
        #
        # Create Subscriptions
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/1/subscriptions',
                                      'POST',
                                      dict(question_id=1, how='asap'),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 201)
        # Log data received
        app.logger.debug("Data retrieved from Create Subscription = %s\n",
                         rv.data)

        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/1/subscriptions',
                                      'POST',
                                      dict(question_id=2, how='asap'),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/1/subscriptions',
                                      'POST',
                                      dict(question_id=3, how='weekly'),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/5/subscriptions',
                                      'POST',
                                      dict(question_id=3, how='daily'),
                                      'harry',
                                      'harry123')
        self.assertEqual(rv.status_code, 201)

        #
        # Update Subscriptions
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/5/subscriptions',
                                      'POST',
                                      dict(question_id=3, how='asap'),
                                      'harry',
                                      'harry123')
        # Log data received
        app.logger.debug("Data retrieved from Update Subscriptions = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201)

        #
        # Get Subscriptions
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/1/subscriptions',
                                      'GET',
                                      dict(),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Subscriptions = %s\n",
                         rv.data)

        #
        # Get question subscribers
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions/3/subscribers',
                                      'GET',
                                      dict(),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Question Subscribers = %s\n",
                         rv.data)

        #
        # Delete Subscription
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/users/1/subscriptions/3',
                                      'DELETE',
                                      dict(),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Delete Subscription = %s\n",
                         rv.data)

        '''
        #
        # Create Proposals
        #
        bills_blurb = '''I have never written anything so comprehensive on a website before.\n\nIIt makes me realise how much fun this can be.
        '''
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals',
            'POST',
            dict(title='Bills First Proposal',
                 blurb=bills_blurb),
            'bill',
            'bill123')
        self.assertEqual(rv.status_code, 201)
        # Log data received
        app.logger.debug("Data retrieved from Create Proposal = %s\n",
                         rv.data)

        bills_other_blurb = '''This is a much better proposal than my first one.\n\nIIt makes me realise how personal growth continues even while using the internet.'''
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals',
            'POST',
            dict(title='Bills Second Proposal',
                 blurb=bills_other_blurb,
                 abstract='This is too abstract for an abstract'),
            'bill',
            'bill123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals',
            'POST',
            dict(title='Susans Only Proposal',
                 blurb='My blub is cool',
                 abstract='Blah blah blah'),
            'susan',
            'susan123')
        self.assertEqual(rv.status_code, 201)

        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals',
            'POST',
            dict(
                title='Harrys Cool Proposal',
                blurb='Harry wrties like a champ'),
            'harry',
            'harry123')
        self.assertEqual(rv.status_code, 201)

        data = json.loads(rv.data)
        new_proposal_uri = data['proposal']['uri']
        app.logger.debug("New propoal URI = %s", new_proposal_uri)

        # Harry edits his proposal
        '''
        rv = self.open_with_json_auth(
            new_proposal_uri,
            'POST',
            dict(
                title='Harrys Cooler Proposal',
                blurb='Harry edits like a champ'),
            'harry',
            'harry123')
        self.assertEqual(rv.status_code, 200, self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved from Edit Proposal = %s\n",
                         rv.data)
        '''

        #
        # Get Proposals
        #
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals',
            'GET',
            dict(),
            'bill',
            'bill123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Question Proposals = %s\n",
                         rv.data)

        #
        # Author attempts to Delete a Question - Disallowed
        # because it has proposals
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions/1',
                                      'DELETE',
                                      dict(),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 403, self.get_message(rv))
        self.assertIn("This question has proposals",
                      self.get_message(rv),
                      self.get_message(rv))
        app.logger.debug("Response message: %s", self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved = %s\n", rv.data)

        #
        # Author moves question on to VOTING phase
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions/1',
                                      'POST',
                                      dict(move_on=True),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 200, self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved from Edit Question (Move On) = %s\n",
                         rv.data)

        #
        # Create then Delete a Proposal.
        # Must be done in the writing phase where the proposal was created.
        #
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/3/proposals',
            'POST',
            dict(
                title="My less than stirling proposal",
                blurb="This is not very good. Think I'll delete it."),
            'harry',
            'harry123')
        app.logger.debug("Data retrieved from Create Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201)
        data = json.loads(rv.data)
        harrys_proposal_uri = data['proposal']['uri']
        #
        # Delete the proposal
        #
        app.logger.debug("Harry deletes his proposal with uri: %s",
                         harrys_proposal_uri)
        rv = self.open_with_json_auth(
            harrys_proposal_uri,
            'DELETE',
            dict(),
            'harry',
            'harry123')
        app.logger.debug("Harry deletes his proposal - message: %s",
                         self.get_message(rv))
        app.logger.debug("Data retrieved from Delete Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 200)


        #
        # Create Endorsements
        #
        # Endorse using votemap coordinates only
        #
        if USE_VOTEMAP:
            # Propoosal 1
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/1/endorsements',
                'POST',
                dict(
                    # endorsement_type="oppose",
                    use_votemap=True,
                    coords={'mapx': 0.75, 'mapy': 0.46}),
                'bill',
                'bill123')
            self.assertEqual(rv.status_code, 201)
            
            # bills_prop1.endorse(john)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/1/endorsements',
                'POST',
                dict(
                    # endorsement_type="endorse",
                    use_votemap=True,
                    coords={'mapx': 0.65, 'mapy': 0.16}),
                'john',
                'john123')
            self.assertEqual(rv.status_code, 201)

            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/1/endorsements',
                'POST',
                dict(
                    # endorsement_type="confused",
                    use_votemap=True,
                    coords={'mapx': 0.631388, 'mapy': 0.634726}),
                'jack',
                'jack123')
            self.assertEqual(rv.status_code, 201)
            
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/1/endorsements',
                'POST',
                dict(
                    # endorsement_type="confused",
                    use_votemap=True,
                    coords={'mapx': 0.497361, 'mapy': 0.598698}),
                'susan',
                'susan123')
            self.assertEqual(rv.status_code, 201)
            
            # bills_prop1.endorse(harry)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/1/endorsements',
                'POST',
                dict(
                    # endorsement_type="endorse",
                    use_votemap=True,
                    coords={'mapx': 0.76, 'mapy': 0.33}),
                'harry',
                'harry123')
            self.assertEqual(rv.status_code, 201)

            # bills_prop2.endorse(bill)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/2/endorsements',
                'POST',
                dict(
                    # endorsement_type="endorse",
                    use_votemap=True,
                    coords={'mapx': 0.5, 'mapy': 0.1}),
                'bill',
                'bill123')
            self.assertEqual(rv.status_code, 201)
            
            # John doesn't understand proposal 2
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/2/endorsements',
                'POST',
                dict(
                    # endorsement_type="confused",
                    use_votemap=True,
                    coords={'mapx': 0.5, 'mapy': 0.7}),
                'john',
                'john123')
            app.logger.debug("Data retrieved from Oppose Proposal = %s\n",
                             rv.data)
            self.assertEqual(rv.status_code, 201, rv.status_code)
            
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/2/endorsements',
                'POST',
                dict(
                    # endorsement_type="confused",
                    use_votemap=True,
                    coords={'mapx': 0.42, 'mapy': 0.77}),
                'jack',
                'jack123')
            self.assertEqual(rv.status_code, 201)
            
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/2/endorsements',
                'POST',
                dict(
                    # endorsement_type="oppose",
                    use_votemap=True,
                    coords={'mapx': 0.2, 'mapy': 0.03}),
                'susan',
                'susan123')
            self.assertEqual(rv.status_code, 201)
            
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/2/endorsements',
                'POST',
                dict(
                    # endorsement_type="oppose",
                    use_votemap=True,
                    coords={'mapx': 0.311503, 'mapy': 0.264203}),
                'harry',
                'harry123')
            self.assertEqual(rv.status_code, 201)

            # susans_prop1.endorse(susan)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsements',
                'POST',
                dict(
                    # endorsement_type="endorse",
                    use_votemap=True,
                    coords={'mapx': 0.55, 'mapy': 0.43}),
                'susan',
                'susan123')
            self.assertEqual(rv.status_code, 201)
            # Log data received
            app.logger.debug("Data retrieved from Create Endorsement = %s\n",
                             rv.data)

            # susans_prop1.endorse(john)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsements',
                'POST',
                dict(
                    # endorsement_type="endorse",
                    use_votemap=True,
                    coords={'mapx': 0.7, 'mapy': 0.1}),
                'john',
                'john123')
            self.assertEqual(rv.status_code, 201)

            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsements',
                'POST',
                dict(
                    # endorsement_type="oppose",
                    use_votemap=True,
                    coords={'mapx': 0.26, 'mapy': 0.3}),
                'bill',
                'bill123')
            self.assertEqual(rv.status_code, 201)
            
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsements',
                'POST',
                dict(
                    # endorsement_type="oppose",
                    use_votemap=True,
                    coords={'mapx': 0.1, 'mapy': 0.13}),
                'jack',
                'jack123')
            self.assertEqual(rv.status_code, 201)
            
            # susans_prop1.endorse(harry)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsements',
                'POST',
                dict(
                    # endorsement_type="endorse",
                    use_votemap=True,
                    coords={'mapx': 0.7, 'mapy': 0.22}),
                'harry',
                'harry123')
            self.assertEqual(rv.status_code, 201)

            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/4/endorsements',
                'POST',
                dict(
                    # endorsement_type="oppose",
                    use_votemap=True,
                    coords={'mapx': 0.3, 'mapy': 0.2}),
                'john',
                'john123')
            app.logger.debug("Data retrieved from Oppose Proposal = %s\n",
                             rv.data)
            self.assertEqual(rv.status_code, 201, rv.status_code)

            # Add OPPOSED endorsement
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/4/endorsements',
                'POST',
                dict(
                    # endorsement_type="oppose",
                    use_votemap=True,
                    coords={'mapx': 0.0910423, 'mapy': 0.153047}),
                'harry',
                'harry123')
            app.logger.debug("Data retrieved from Oppose Proposal = %s\n",
                             rv.data)
            self.assertEqual(rv.status_code, 201, rv.status_code)

            # Add Confused endorsement
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/4/endorsements',
                'POST',
                dict(
                    # endorsement_type="confused",
                    use_votemap=True,
                    coords={'mapx': 0.5, 'mapy': 0.9}),
                'bill',
                'bill123')
            app.logger.debug("Data retrieved from Confused by Proposal = %s\n",
                             rv.data)
            self.assertEqual(rv.status_code, 201, rv.status_code)

            # harrys_prop1.endorse(jack)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/4/endorsements',
                'POST',
                dict(
                    # endorsement_type="endorse",
                    use_votemap=True,
                    coords={'mapx': 0.6, 'mapy': 0.3}),
                'jack',
                'jack123')
            self.assertEqual(rv.status_code, 201)

            # harrys_prop1.endorse(susan)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/4/endorsements',
                'POST',
                dict(
                    # endorsement_type="endorse",
                    use_votemap=True,
                    coords={'mapx': 0.55, 'mapy': 0.22}),
                'susan',
                'susan123')
            self.assertEqual(rv.status_code, 201)

            #
            # Create a consensus?
            #
            if CREATE_CONSENSUS:
                rv = self.open_with_json_auth(
                    api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsements',
                    'POST',
                    dict(
                        use_votemap=True,
                        coords={'mapx': 0.56, 'mapy': 0.21}),
                    'bill',
                    'bill123')
                self.assertEqual(rv.status_code, 201)

                rv = self.open_with_json_auth(
                    api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsements',
                    'POST',
                    dict(
                        use_votemap=True,
                        coords={'mapx': 0.57, 'mapy': 0.20}),
                    'jack',
                    'jack123')
                self.assertEqual(rv.status_code, 201)

        # else Endorse using endorsement type instead of votemap coordinates
        #
        else:
            # susans_prop1.endorse(susan)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsements',
                'POST',
                dict(endorsement_type="endorse"),
                'susan',
                'susan123')
            self.assertEqual(rv.status_code, 201)
            # Log data received
            app.logger.debug("Data retrieved from Create Endorsement = %s\n",
                             rv.data)

            # susans_prop1.endorse(john)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsements',
                'POST',
                dict(endorsement_type="endorse"),
                'john',
                'john123')
            self.assertEqual(rv.status_code, 201)

            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/4/endorsements',
                'POST',
                dict(endorsement_type="oppose"),
                'john',
                'john123')
            app.logger.debug("Data retrieved from Oppose Proposal = %s\n",
                             rv.data)
            self.assertEqual(rv.status_code, 201, rv.status_code)

            # John doesn't understand proposal 2
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/2/endorsements',
                'POST',
                dict(endorsement_type="confused"),
                'john',
                'john123')
            app.logger.debug("Data retrieved from Oppose Proposal = %s\n",
                             rv.data)
            self.assertEqual(rv.status_code, 201, rv.status_code)

            # Add OPPOSED endorsement
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/4/endorsements',
                'POST',
                dict(endorsement_type="oppose"),
                'harry',
                'harry123')
            app.logger.debug("Data retrieved from Oppose Proposal = %s\n",
                             rv.data)
            self.assertEqual(rv.status_code, 201, rv.status_code)

            # Add Confused endorsement
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/4/endorsements',
                'POST',
                dict(endorsement_type="confused"),
                'bill',
                'bill123')
            app.logger.debug("Data retrieved from Confused by Proposal = %s\n",
                             rv.data)
            self.assertEqual(rv.status_code, 201, rv.status_code)
        
            # bills_prop1.endorse(john)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/1/endorsements',
                'POST',
                dict(endorsement_type="endorse"),
                'john',
                'john123')
            self.assertEqual(rv.status_code, 201)

            # bills_prop2.endorse(bill)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/2/endorsements',
                'POST',
                dict(endorsement_type="endorse"),
                'bill',
                'bill123')
            self.assertEqual(rv.status_code, 201)

            # harrys_prop1.endorse(jack)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/4/endorsements',
                'POST',
                dict(endorsement_type="endorse"),
                'jack',
                'jack123')
            self.assertEqual(rv.status_code, 201)

            # harrys_prop1.endorse(susan)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/4/endorsements',
                'POST',
                dict(endorsement_type="endorse"),
                'susan',
                'susan123')
            self.assertEqual(rv.status_code, 201)

            # bills_prop1.endorse(harry)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/1/endorsements',
                'POST',
                dict(endorsement_type="endorse"),
                'harry',
                'harry123')
            self.assertEqual(rv.status_code, 201)

            # susans_prop1.endorse(harry)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsements',
                'POST',
                dict(endorsement_type="endorse"),
                'harry',
                'harry123')
            self.assertEqual(rv.status_code, 201)
        #
        ########################################## Endorsements


        #
        # Comments, oppose, confused
        #
        # Add a comment only
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/4/comments',
            'POST',
            dict(
                comment_type="against",
                comment="This is terrible!"),
                'john',
                'john123')
        app.logger.debug("Data retrieved from Confused by Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201, rv.status_code)

        # Add a comment only
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/4/comments',
            'POST',
            dict(
                comment_type="against",
                comment="This is terrible!"),
                'harry',
                'harry123')
        app.logger.debug("Data retrieved from Confused by Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 400, rv.status_code)

        # Add support to comment
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/4/comments/1/support',
            'POST',
            dict(),
            'harry',
            'harry123')
        app.logger.debug("Data retrieved from supporting comment 1 = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201, rv.status_code)

        # Add a comment
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/4/comments',
            'POST',
            dict(
                comment_type="question",
                comment="This is rubbish! How much would this cost?"),
                'susan',
                'susan123')
        app.logger.debug("Data retrieved from Confused by Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201, rv.status_code)

        # Add a comment
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/4/comments',
            'POST',
            dict(
                comment_type="answer",
                comment="About 1.2 bitcoins, more or less.",
                reply_to=2),
                'john',
                'john123')
        app.logger.debug("Data retrieved from Confused by Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201, rv.status_code)

        # Add a comment
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/4/comments',
            'POST',
            dict(
                comment_type="against",
                comment="I think this sucks bigtime, baby! It would cost too much and we will all go broke."),
                'bill',
                'bill123')
        app.logger.debug("Data retrieved from Confused by Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201, rv.status_code)

        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/3/comments',
            'POST',
            dict(
                comment_type="for",
                comment="This will work bigtime. It could be coded in python."),
                'john',
                'john123')
        app.logger.debug("Data retrieved from Confused by Proposal = %s\n",
                         rv.data)
        self.assertEqual(rv.status_code, 201, rv.status_code)

        #
        # Get comments
        #
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/4/comments',
            'GET',
            dict(),
            'john',
            'john123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Comments = %s\n", rv.data)

        #
        # Get Proposals
        #
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals',
            'GET',
            dict(),
            'bill',
            'bill123')
        self.assertEqual(rv.status_code, 200)
        # Log data received
        app.logger.debug("Data retrieved from Get Question Proposals after endorsements = %s\n",
                         rv.data)

        #
        # Get Proposal Endorsers
        #
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/3/endorsers',
            'GET',
            dict(),
            'harry',
            'harry123')
        self.assertEqual(rv.status_code, 200, rv.status_code)
        app.logger.debug("Data retrieved = %s\n", rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Get Proposal Endorsers = %s\n",
                         rv.data)

        #
        # Get Question Pareto
        #
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/pareto',
            'GET',
            dict(),
            'harry',
            'harry123')
        self.assertEqual(rv.status_code, 200, rv.status_code)
        app.logger.debug("Data retrieved = %s\n", rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Get Question Pareto = %s\n",
                         rv.data)

        #
        # Get Key Players
        #
        '''
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/key_players',
            'GET',
            dict(),
            'harry',
            'harry123')
        self.assertEqual(rv.status_code, 200, rv.status_code)
        app.logger.debug("Data retrieved = %s\n", rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Get Key Players = %s\n",
                         rv.data)
        '''

        #
        # Get Endorser Effects
        #
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/endorser_effects',
            'GET',
            dict(),
            'harry',
            'harry123')
        self.assertEqual(rv.status_code, 200, rv.status_code)
        app.logger.debug("Endorser Effects data retrieved = %s\n", rv.data)
        # Log data received
        app.logger.debug("Data retrieved from Get Endorser Effects= %s\n",
                         rv.data)

        #
        # Get Proposal Relations
        #
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposal_relations',
            'GET',
            dict(),
            'harry',
            'harry123')
        self.assertEqual(rv.status_code, 200, rv.status_code)
        # Log data received
        app.logger.debug("Data retrieved from Get Proposal Relations = %s\n",
                         rv.data)

        if MAKE_GRAPH:
            #
            # Create Voting Map
            #
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/graph?generation=1&map_type=all',
                'GET',
                dict(),
                'harry',
                'harry123')
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            app.logger.debug("Data retrieved from get graph = %s\n", data)
            # self.assertIn('map_Q1_G1_all_1_1.svg', data['url'],
            #              "File URL not returned")

            if app.config['ALGORITHM_VERSION'] == 1:

                rv = self.open_with_json_auth(
                    api.REST_URL_PREFIX + '/questions/1/graph?generation=1&map_type=pareto',
                    'GET',
                    dict(),
                    'harry',
                    'harry123')
                self.assertEqual(rv.status_code, 200)
                data = json.loads(rv.data)
                app.logger.debug("Data retrieved from get graph = %s\n", data)
                # self.assertIn('map_Q1_G1_all_1_1.svg', data['url'],
                #              "File URL not returned")
            
                # Stop here while debugging graph

        
        # gen 2
        if MOVE_TO_GENERATION_2:
            #
            # Author moves question on to WRITING phase and GENERATION 2
            #
            app.logger.debug("Move question on to next generation")
            rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions/1',
                                          'POST',
                                          dict(move_on=True),
                                          'john',
                                          'john123')
            self.assertEqual(rv.status_code, 200, self.get_message(rv))
            # Log data received
            app.logger.debug("Data retrieved from Edit Question (Move On) = %s\n",
                             rv.data)
            
            #
            # Create Proposals
            #
            bills_blurb = '''This is getting interesting. I may stay up all night deliberating.
            '''
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals',
                'POST',
                dict(title='Bills 2nd Gen Proposal',
                     blurb=bills_blurb),
                'bill',
                'bill123')
            self.assertEqual(rv.status_code, 201)
            # Log data received
            app.logger.debug("Data retrieved from Create Proposal = %s\n",
                             rv.data)

            bills_other_blurb = '''Once I've finished writing this I'm going to sell the rights to warner Brother.'''
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals',
                'POST',
                dict(title='Bills Round 2 Proposal for Hollywood',
                     blurb=bills_other_blurb,
                     abstract='This is too expressionistic for an abstract'),
                'bill',
                'bill123')
            self.assertEqual(rv.status_code, 201)
            
            # Propoosal 1
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/1/endorsements',
                'POST',
                dict(
                    # endorsement_type="oppose",
                    use_votemap=True,
                    coords={'mapx': 0.75, 'mapy': 0.46}),
                'bill',
                'bill123')
            self.assertEqual(rv.status_code, 201)
            
            # bills_prop1.endorse(john)
            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/1/endorsements',
                'POST',
                dict(
                    # endorsement_type="endorse",
                    use_votemap=True,
                    coords={'mapx': 0.65, 'mapy': 0.16}),
                'john',
                'john123')
            self.assertEqual(rv.status_code, 201)

            rv = self.open_with_json_auth(
                api.REST_URL_PREFIX + '/questions/1/proposals/1/endorsements',
                'POST',
                dict(
                    # endorsement_type="confused",
                    use_votemap=True,
                    coords={'mapx': 0.68, 'mapy': 0.67}),
                'jack',
                'jack123')
            self.assertEqual(rv.status_code, 201)
        
        
        
        #
        # Update Endorsements
        #
        '''
        # John ID=1 endorses proposal 2
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/2/endorsements',
            'POST',
            dict(ndorsement_type="endorse"),
            'john',
            'john123')
        self.assertEqual(rv.status_code, 201)
        
        
        #
        # Updates endorsement to OPPOSE
        app.logger.debug("John updates his endopsement to OPPOSE")
        rv = self.open_with_json_auth(
            api.REST_URL_PREFIX + '/questions/1/proposals/2/endorsements',
            'POST',
            dict(endorsement_type='oppose'),
            'john',
            'john123')
        self.assertEqual(rv.status_code, 200, self.get_message(rv))
        self.assertEqual("Endorsement updated",
                         self.get_message(rv),
                         self.get_message(rv))
        app.logger.debug("Response message: %s", self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved from Update Endorsement = %s\n",
                         rv.data)
        '''

        #
        # Create Another Question
        #
        rv = self.open_with_json_auth(api.REST_URL_PREFIX + '/questions',
                                      'POST',
                                      dict(title='My boring question',
                                           blurb='My boring blurb'),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 201)
        data = json.loads(rv.data)
        app.logger.debug("New question at = %s\n", data['question']['url'])
        new_question_url = data['question']['url']

        #
        # Author Deletes Question
        #
        rv = self.open_with_json_auth(new_question_url,
                                      'DELETE',
                                      dict(),
                                      'john',
                                      'john123')
        self.assertEqual(rv.status_code, 200, self.get_message(rv))
        self.assertIn("Question deleted",
                      self.get_message(rv),
                      self.get_message(rv))
        app.logger.debug("Response message: %s", self.get_message(rv))
        # Log data received
        app.logger.debug("Data retrieved from Delete Question = %s\n",
                         rv.data)

    def get_questions(self):
        rv = self.app.get(api.REST_URL_PREFIX + '/users')
        #  rv = self.open_with_auth(
        #    api.REST_URL_PREFIX + '/users', 'GET', None, 'grippo', 'test123')
        app.logger.debug("Data retrieved = %s\n", rv.data)
        self.assertEqual(rv.status_code, 200)

        rv = self.open_with_auth(api.REST_URL_PREFIX + '/users/50', 'GET',
                                 None, 'grippo', 'test123')
        app.logger.debug("Data retrieved = %s\n", rv.data)

        data = json.loads(rv.data)
        self.assertNotIn('email', data['object'])

        rv = self.open_with_auth(api.REST_URL_PREFIX + '/users/638', 'GET',
                                 None, 'grippo', 'test123')
        app.logger.debug("Data retrieved = %s\n", rv.data)

        data = json.loads(rv.data)
        app.logger.debug("Email retrieved = %s\n", data['object']['email'])
        self.assertIn('email', data['object'])

    def empty_db(self):
        """Start with a blank database."""
        rv = self.app.get('/')
        self.assertTrue('no questions' in rv.data, rv.data)
