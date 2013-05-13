# -*- coding: utf-8 -*-
#
# This file is part of VilfredoReloadedCore.
#
# Copyright (c) 2013 Derek Paterson <athens_code@gmx.com>
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

from .. import models, app

from .. import views  # NOQA

from .. database import db_session, drop_db, init_db


class UserTest(unittest.TestCase):
    def setUp(self):
        init_db()

    def tearDown(self):
        drop_db()
        db_session.remove()

    def test_create_user(self):
        user = models.User('test_username', 'test_email', 'test_password')
        db_session.add(user)
        db_session.commit()
        user1 = models.User.query.filter(
            models.User.username == 'test_username'
        ).first()
        self.assertEqual(user.email, user1.email)
        self.assertTrue(user1.is_active())
        new_username = 'test_username'
        self.assertFalse(
            models.User.username_available(new_username))
        new_email = 'test_email'
        self.assertFalse(
            models.User.email_available(new_email))


class QuestionTest(unittest.TestCase):
    def setUp(self):
        init_db()

    def tearDown(self):
        drop_db()
        db_session.remove()

    def test_create_question(self):
        user = models.User('test_username_1', 'test_email_1', 'test_password')
        db_session.add(user)
        db_session.commit()
        question = models.Question(
            user, 'Question Title',
            'Question content')
        db_session.add(question)
        db_session.commit()
        question1 = models.Question.query.filter(
            models.Question.title == 'Question Title'
        ).first()
        self.assertEqual(question1.blurb, 'Question content')
        self.assertEqual(question1.author.username, user.username)
        # Check questions pareto is empty
        self.assertEquals(question1.calculate_pareto_front(), set(),
                          "PF failed to return an empty set")


class SubscriptionTest(unittest.TestCase):
    def setUp(self):
        init_db()

    def tearDown(self):
        drop_db()
        db_session.remove()

    def test_create_question_subscription(self):
        user = models.User('test_username', 'test_email', 'test_password')
        db_session.add(user)
        db_session.commit()
        question = models.Question(
            user, 'Question Title',
            'Question content')
        db_session.add(question)
        db_session.commit()

        user.subscribe_to(question)
        db_session.commit()

        update = models.Update.query.filter(
            models.Update.user_id == user.id
        ).first()
        self.assertEqual(update.question_id, question.id)

        self.assertTrue(user.is_subscribed_to(question))
        user.unsubscribe_from(question)
        db_session.commit()
        self.assertFalse(user.is_subscribed_to(question))


class ProposalTest(unittest.TestCase):
    def setUp(self):
        init_db()

    def tearDown(self):
        drop_db()
        db_session.remove()

    def test_create_proposal(self):
        user = models.User('test_username', 'test_email', 'test_password')
        db_session.add(user)
        db_session.commit()

        question = models.Question(
            user, 'Question Title',
            'Question content')
        db_session.add(question)
        db_session.commit()

        proposal = models.Proposal(
            user, question, 'Proposal Title',
            'Proposal content')
        db_session.add(proposal)
        db_session.commit()

        proposal1 = models.Proposal.query.filter(
            models.Proposal.title == 'Proposal Title'
        ).first()
        self.assertEqual(proposal1.blurb, 'Proposal content')
        self.assertEqual(proposal1.author.username, user.username)

        print "Fetch proposals for this generation"
        current_proposals = question.get_proposals()
        self.assertTrue(type(current_proposals) is list)
        self.assertEquals(len(current_proposals), 1)

        print "Fetch USER'S proposals for this generation of this question"
        user_question_proposals = user.get_proposals(question)
        users_proposal = user_question_proposals[0]
        self.assertEqual(users_proposal, proposal)

        proposal_id = users_proposal.id

        # Add second user
        user2 = models.User('user 2', 'email_for_user2', 'password')
        db_session.add(user2)
        db_session.commit()

        print "Another user attempts to edit proposal"
        users_proposal.update(user2, 'Edited Title', 'New improved blurb')
        db_session.commit()
        print "Fetch USER'S proposals for this generation of this question"
        fetch_prop = models.Proposal.query.get(proposal_id)
        self.assertEqual(fetch_prop.title, 'Proposal Title', fetch_prop.title)

        update_prop = users_proposal.update(user,
                                            'Edited Title',
                                            'New improved blurb')
        self.assertTrue(update_prop, update_prop)
        db_session.commit()
        print "Fetch USER'S proposals for this generation of this question"
        fetch_prop = models.Proposal.query.get(proposal_id)
        self.assertEqual(fetch_prop.title, 'Edited Title', fetch_prop.title)

        user.delete_proposal(users_proposal)
        db_session.commit()

        print "Fetch USER'S proposals for this generation of this question"
        fetch_prop = models.Proposal.query.get(proposal_id)
        self.assertTrue(fetch_prop is None, fetch_prop)


class EndorseTest(unittest.TestCase):
    def setUp(self):
        init_db()

    def tearDown(self):
        db_session.remove()
        drop_db()

    def test_endorse_proposals(self):
        # Create users
        john = models.User('john', 'john@example.com', 'fgfdfg')
        susan = models.User('susan', 'susan@example.com', 'bgtyhj')
        bill = models.User('bill', 'bill@example.com', 'h6ygf')
        jack = models.User('jack', 'jack@example.com', 'kjkjkjkj')
        harry = models.User('harry', 'harry@example.com', 'gfgrd')

        db_session.add_all([john, susan, bill, jack, harry])
        db_session.commit()

        # Create questions
        johns_q = models.Question(
            john, 'Johns Question',
            'What shall we do with the plutonium')
        johns_q2 = models.Question(
            john, 'Johns Other Question',
            'What shall we do with the uranium')

        db_session.add_all([johns_q, johns_q2])
        db_session.commit()

        # Fetch list of users for john's invite selection
        user_query = \
            models.User.query.filter(
                models.User.id != john.id) \
            .order_by(models.User.username).limit(20)
        #user_list = models.User.query.limit(4).all()
        #self.assertEquals(len(user_list), 4)
        self.assertEquals(user_query.count(), 4)

        # Create invitations (user invites users)
        john.invite(susan, johns_q)
        john.invite(bill, johns_q)
        john.invite(bill, johns_q2)
        db_session.commit()
        for inv in john.invites:
            print "Invitation for question ", inv.question_id,
            " sent to user ",
            inv.receiver.username

        print "Bills invitations"
        for inv in bill.invitations:
            print inv.question_id, " from author ", inv.sender.username

        # Creating proposals
        bills_prop1 = models.Proposal(
            bill, johns_q, 'Bills First Proposal',
            'Bills blurb of varying interest')
        bills_prop2 = models.Proposal(
            bill, johns_q, 'Bills Second Proposal',
            'Bills blurb of varying disinterest')
        susans_prop1 = models.Proposal(
            susan, johns_q, 'Susans Only Proposal',
            'My blub is cool')

        db_session.add_all([bills_prop1, bills_prop2, susans_prop1])
        db_session.commit()
        print "Current proposal ids", johns_q.current_proposals_ids()

        # Subscribing users to questions
        bill.subscribe_to(johns_q)
        susan.subscribe_to(johns_q)
        db_session.commit()

        # Let the endorsements commence
        susans_prop1.endorse(susan)
        susans_prop1.endorse(john)
        bills_prop1.endorse(john)
        bills_prop2.endorse(bill)
        db_session.commit()

        print "Proposal ID", bills_prop1.id, "with endorses:",\
            bills_prop1.set_of_endorser_ids()
        print "Proposal ID", bills_prop2.id, "with endorses:",\
            bills_prop2.set_of_endorser_ids()
        print "Proposal ID", susans_prop1.id, "with endorses:",\
            susans_prop1.set_of_endorser_ids()

        # PF???
        pf = johns_q.calculate_pareto_front()
        print "Pareto Front is", pf
        self.assertEqual(pf, {2, 3}, pf)

        # Get a list of the current endorsers
        current_endorsers = susans_prop1.endorsers()
        self.assertTrue(type(current_endorsers) is set)

        current_endorser_ids = susans_prop1.set_of_endorser_ids()
        self.assertEqual(current_endorser_ids, {susan.id, john.id})

        endorsements = models.Endorsement.query.filter(
            models.Endorsement.proposal_id == susans_prop1.id).count()
        self.assertEqual(endorsements, 2)
        endorsements = models.Endorsement.query.filter(
            models.Endorsement.proposal_id == bills_prop1.id).count()
        self.assertEqual(endorsements, 1)
        endorsements = models.Endorsement.query.filter(
            models.Endorsement.proposal_id == bills_prop2.id).count()
        self.assertEqual(endorsements, 1)

        susans_prop1_endorsers = set()
        endorsements = models.Endorsement.query.filter(
            models.Endorsement.proposal_id == susans_prop1.id)
        for endorsement in endorsements:
            susans_prop1_endorsers.add(endorsement.endorser)
        self.assertTrue(susan in susans_prop1_endorsers)
        self.assertTrue(john in susans_prop1_endorsers)
        self.assertFalse(bill in susans_prop1_endorsers)

        # Test proposal's is_endorse_by method
        self.assertTrue(susans_prop1.is_endorsed_by(susan))
        self.assertFalse(susans_prop1.is_endorsed_by(bill))

        # Remove endorsement
        susans_prop1.remove_endorsement(susan)
        db_session.commit()
        self.assertFalse(susans_prop1.is_endorsed_by(susan))


class TestWhoDominatesWho(unittest.TestCase):
    def setUp(self):
        init_db()

    def tearDown(self):
        drop_db()
        db_session.remove()

    def test_proposal_domination(self):
        p1 = {1, 2, 3}
        p2 = {2, 3, 4, 5, 6, 7}
        p3 = {1, 2, 7, 8, 9, 10}
        p4 = {4, 5, 6}
        p5 = {4, 5, 6}
        p6 = set()
        p7 = set()
        self.assertEqual(models.Proposal.who_dominates_who(p2, p4), p2)
        self.assertEqual(models.Proposal.who_dominates_who(p4, p5), -1)
        self.assertEqual(models.Proposal.who_dominates_who(p2, p3), 0)
        self.assertEqual(models.Proposal.who_dominates_who(p6, p7), -1)
        self.assertEqual(models.Proposal.who_dominates_who(p1, p7), p1)

        self.assertEqual(models.Proposal.who_dominates_who_2(p2, p4), p2)
        self.assertEqual(models.Proposal.who_dominates_who_2(p4, p5), -1)
        self.assertEqual(models.Proposal.who_dominates_who_2(p2, p3), 0)
        self.assertEqual(models.Proposal.who_dominates_who_2(p6, p7), -1)
        self.assertEqual(models.Proposal.who_dominates_who_2(p1, p7), p1)


class LoginTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        init_db()

    def tearDown(self):
        drop_db()
        db_session.remove()

    def test_empty_db(self):
        """Start with a blank database."""
        rv = self.app.get('/')
        self.assertTrue('No questions here so far' in rv.data, rv.data)

    def test_login_logout(self):
        rv = self.login('test_user', 'test_password')
        self.assertTrue('You were logged in' in rv.data, rv.data)
        rv = self.logout()
        self.assertTrue('You were logged out' in rv.data, rv.data)
        rv = self.login('unknown_user', 'test_password')
        self.assertTrue('Invalid username' in rv.data, rv.data)
        rv = self.login('test_user', 'wrong_password')
        self.assertTrue('Invalid password' in rv.data, rv.data)

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)


class RegisterTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        init_db()
        self.add_existing_user()

    def tearDown(self):
        drop_db()
        db_session.remove()

    def test_register(self):
        # Test for empty fields
        rv = self.register('', 'test_email', 'test_password')
        self.assertTrue('Invalid username' in rv.data, rv.data)
        rv = self.register('test_user', 'test_email', '')
        self.assertTrue('Invalid password' in rv.data, rv.data)
        rv = self.register('test_user', '', 'test_password')
        self.assertTrue('Invalid email' in rv.data, rv.data)
        # Check DB for username and email
        rv = self.register('user', 'test_email', 'test_password')
        self.assertTrue('Username not available' in rv.data, rv.data)
        rv = self.register('test_user', 'email', 'test_password')
        self.assertTrue('Email not available' in rv.data, rv.data)
        # Register user with correct details
        rv = self.register('test_user', 'test_email', 'test_password')
        self.assertTrue('You have been registered' in rv.data, rv.data)

    def register(self, username, email, password):
        return self.app.post('/register', data=dict(
            username=username,
            email=email,
            password=password
        ), follow_redirects=True)

    def add_existing_user(self):
        existing_user = models.User('user', 'email', 'test_password')
        db_session.add(existing_user)
        db_session.commit()
