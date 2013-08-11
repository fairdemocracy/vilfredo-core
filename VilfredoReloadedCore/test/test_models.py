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

from .. import models, app, emails, mail
from .. import views  # NOQA
from .. database import db_session, drop_db, init_db
import datetime
import time
import os

DELETE_DB_ON_EXIT = True


def setUpDB():
    # For SQLite development DB only
    if 'vr.db' in app.config['SQLALCHEMY_DATABASE_URI']:
        # Drop existing DB first
        if os.path.isfile('/var/tmp/vr.db'):
            app.logger.debug("Dropping existing sqlite db\n")
            drop_db()
        # Create empty SQLite test DB
        app.logger.debug("Initializing sqlite db\n")
        init_db()


def tearDownDB():
    # For SQLite development DB only
    if 'vr.db' in app.config['SQLALCHEMY_DATABASE_URI'] \
            and DELETE_DB_ON_EXIT:
        app.logger.debug("Dropping sqlite db\n")
        drop_db()


class PasswordHashTest(unittest.TestCase):
    def test_password_hash(self):
        """Test password hasher."""
        from werkzeug.security import check_password_hash,\
            generate_password_hash
        p = 'passwd'
        h = generate_password_hash(p)

        self.assertTrue(check_password_hash(h, p))
        self.assertFalse(check_password_hash(h, p + '1'))


class UserTest(unittest.TestCase):
    def setUp(self):
        setUpDB()

    def tearDown(self):
        tearDownDB()
        db_session.remove()

    def test_create_user(self):
        user = models.User('test_username', 'test_email', 'test_password')
        db_session.add(user)
        db_session.commit()

        self.assertTrue(user.check_password('test_password'))
        self.assertFalse(user.check_password('test_password_bad'))

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
        setUpDB()

    def tearDown(self):
        tearDownDB()
        db_session.remove()

    def time_passed_dhm(self, timestamp):
        td = datetime.datetime.utcfromtimestamp(time.time()) -\
            datetime.datetime.utcfromtimestamp(timestamp)
        return {'days': td.days,
                'hours': td.seconds//3600,
                'minutes': (td.seconds//60) % 60}

    def test_create_question(self):
        user = models.User('test_username_1', 'test_email_1', 'test_password')
        db_session.add(user)
        db_session.commit()
        min_time = 60
        max_time = 220000
        question = models.Question(
            user, 'Question Title',
            'Question content', min_time, max_time)

        question.last_move_on = datetime.datetime(2013, 5, 13, 10, 45)
        question.created = datetime.datetime(2013, 5, 13, 9, 15)

        db_session.add(question)
        db_session.commit()
        question1 = models.Question.query.filter(
            models.Question.title == 'Question Title'
        ).first()
        self.assertEqual(question1.blurb, 'Question content')
        self.assertEqual(question1.author.username, user.username)
        # Check questions pareto is empty
        self.assertEquals(question1.calculate_pareto_front_ids(), set(),
                          "PF failed to return an empty set")
        # pareto_front_2
        self.assertEquals(question1.calculate_pareto_front(), set(),
                          "PF failed to return an empty set")

        # Get time since last_move_on timestamp as days, hours, minutes
        app.logger.debug("Last move on %s\n", question1.last_move_on)
        app.logger.debug("Time passed since last move %s\n",
                         models.Question.time_passed_as_string(
                             question1.last_move_on))

        app.logger.debug('Time passed since created = %s\n',
                         models.Question.time_passed_as_string(
                             question1.created))

        q2 = models.Question(
            user, 'Question 2',
            'Question content 2')
        q3 = models.Question(
            user, 'Question 3',
            'Question content 3')
        q4 = models.Question(
            user, 'Question 4',
            'Question content 4')
        q5 = models.Question(
            user, 'Question 5',
            'Question content 5')
        # Make q4 and q5 voting
        q4.phase = 'voting'
        q5.phase = 'voting'
        db_session.add_all([q2, q3, q4, q5])
        db_session.commit()

         # Fetch all questions
        all_questions = models.Question.query.all()
        self.assertEqual(len(all_questions), 5)

        # Fetch questions in writing phase
        questions_writing = models.Question.query.filter(
            models.Question.phase == 'writing').all()
        self.assertEqual(len(questions_writing), 3)
        for qw in questions_writing:
            self.assertEqual(qw.phase, 'writing', qw.phase)
        # Fetch questions in voting phase
        questions_voting = models.Question.query.filter(
            models.Question.phase == 'voting').all()
        self.assertEqual(len(questions_voting), 2)
        for qv in questions_voting:
            self.assertEqual(qv.phase, 'voting', qv.phase)


class SubscriptionTest(unittest.TestCase):
    def setUp(self):
        setUpDB()

    def tearDown(self):
        tearDownDB()
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
        setUpDB()

    def tearDown(self):
        tearDownDB()
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
        self.assertTrue(type(current_proposals) is set)
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

        # STOP !!!
        # self.assertTrue(False)

        user.delete_proposal(users_proposal)
        db_session.commit()

        # Sself.assertTrue(False)

        print "Fetch USER'S proposals for this generation of this question"
        fetch_prop = models.Proposal.query.get(proposal_id)
        self.assertTrue(fetch_prop is None, fetch_prop)

        # STOP !!!
        # self.assertTrue(False)


class EndorseTest(unittest.TestCase):
    def setUp(self):
        db_session.remove()
        setUpDB()

    def tearDown(self):
        tearDownDB()
        db_session.remove()

    def test_endorse_proposals(self):
        # STOP !!!
        #self.assertTrue(False)
        send_emails = False
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

        '''
        #TEST Foreign Key Constraints is working in SQLite
        ins = models.Question.__table__.insert().values(
            id = 99,
            title = 'Wrong',
            blurb = 'Wrong',
            generation = 1,
            user_id = 99)  # invalid foreign key id

        db_session.execute(ins)
        '''

        # Fetch list of users for john's invite selection
        user_query = \
            models.User.query.filter(
                models.User.id != john.id) \
            .order_by(models.User.username).limit(20)
        #user_list = models.User.query.limit(4).all()
        #self.assertEquals(len(user_list), 4)
        self.assertEquals(user_query.count(), 4)

        # Create invitations (user invites users)
        # john.invite(susan, johns_q)
        # john.invite(bill, johns_q)
        john.invite_all([susan, bill], johns_q)
        john.invite(bill, johns_q2)
        db_session.commit()
        for inv in john.invites:
            print "Invitation for question ", inv.question_id,
            " sent to user ",
            inv.receiver.username

        print "Bills invitations"
        for inv in bill.invitations:
            print inv.question_id, " from author ", inv.sender.username

        if (send_emails):
            # Email invited users
            with mail.record_messages() as outbox:
                emails.email_question_invite(john, susan, johns_q)
                emails.email_question_invite(john, bill, johns_q)
                self.assertEqual(len(outbox), 2)

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

        harrys_prop1 = models.Proposal(
            harry, johns_q, 'Harrys Cool Proposal',
            'Harry wrties like a champ')

        db_session.add_all([bills_prop1, bills_prop2,
                            susans_prop1, harrys_prop1])
        db_session.commit()
        print "Current proposal ids", johns_q.get_proposal_ids()

        # Subscribing users to questions
        bill.subscribe_to(johns_q)
        susan.subscribe_to(johns_q)
        db_session.commit()

        # Let the endorsements commence
        susans_prop1.endorse(susan)
        susans_prop1.endorse(john)
        bills_prop1.endorse(john)
        bills_prop2.endorse(bill)

        harrys_prop1.endorse(jack)
        harrys_prop1.endorse(susan)

        bills_prop1.endorse(harry)
        susans_prop1.endorse(harry)
        db_session.commit()

        # rest here

        print "Proposal ID", bills_prop1.id, "with endorses:",\
            bills_prop1.set_of_endorser_ids()
        print "Proposal ID", bills_prop2.id, "with endorses:",\
            bills_prop2.set_of_endorser_ids()
        print "Proposal ID", susans_prop1.id, "with endorses:",\
            susans_prop1.set_of_endorser_ids()

        # PF???
        pf_props = johns_q.calculate_pareto_front()
        app.logger.debug("Pareto Front = %s\n",
                         pf_props)
        pf = johns_q.calculate_pareto_front_ids()
        app.logger.debug("Set of Pareto Front proposal IDs is %s\n", pf)
        self.assertEqual(pf, {2, 3, 4}, pf)
        # pareto_front, and save in DB
        pf_props = johns_q.calculate_pareto_front(save=True)
        db_session.commit()
        app.logger.debug("Set of Pareto Front proposals is %s\n", pf_props)
        # key players
        key_players = johns_q.calculate_key_players()
        app.logger.debug("johns_q key players = %s\n", key_players)
        all_users = models.User.query.all()
        app.logger.debug("Users are %s\n", all_users)
        # Save key players to the database
        db_session.commit()
        # Calculate endorser effects
        endorser_effects = johns_q.calculate_endorser_effects()
        app.logger.debug("Effect of each endorser: %s\n", endorser_effects)
        #
        for (endorser, effect) in endorser_effects.iteritems():
            if (effect is None):
                app.logger.debug("%s's votes had no effect "
                                 "on the Pareto Front\n",
                                 endorser.username)
            else:
                app.logger.debug("%s's votes did effect the Pareto Front\n",
                                 endorser.username)
                if (len(effect['PF_minus'])):
                    app.logger.debug("Without %s proposals %s "
                                     "would NOT have been on "
                                     "the Pareto Front\n",
                                     endorser.username,
                                     effect['PF_minus'])
                elif (len(effect['PF_plus'])):
                    app.logger.debug("Without %s proposals %s "
                                     "would have been on "
                                     "the Pareto Front\n",
                                     endorser.username,
                                     effect['PF_plus'])

        history = models.QuestionHistory.query.filter(
            models.QuestionHistory.question_id == johns_q.id
        ).all()
        history = models.QuestionHistory.query.all()
        for entry in history:
            print "History: Proposal", entry.proposal_id,\
                'for question', entry.question_id

        # '''
        generation_1 = johns_q.get_generation(1)
        #app.logger.debug("generation_1 = %s\n", generation_1)

        gen_1_proposals = generation_1.proposals
        app.logger.debug("generation_1 has %s proposals\n",
                         len(gen_1_proposals))
        #app.logger.debug("generation_1 proposals are %s\n", gen_1_proposals)

        gen_1_pareto = generation_1.pareto_front

        app.logger.debug("Generation 1 has %s proposals in the pareto front\n",
                         len(gen_1_pareto))

        app.logger.debug("Generation 1 Pareto is %s\n", gen_1_pareto)

        app.logger.debug("Generation 1 Endorsers are %s\n",
                         generation_1.endorsers)

        app.logger.debug("Generation 1 Key Players are %s\n",
                         generation_1.key_players)

        # Recalculate key players for this geenration
        app.logger.debug(
            "Generation 1 Key Players **** Recalculated **** are %s\n",
            generation_1.calculate_key_players())

        gen_1_endorser_effects = generation_1.endorser_effects

        app.logger.debug("Generation 1 Endorser Effects are %s\n",
                         generation_1.endorser_effects)

        for (endorser, effect) in gen_1_endorser_effects.iteritems():
            if (effect is None):
                app.logger.debug("%s's votes had no effect "
                                 "on the Pareto Front\n",
                                 endorser.username)
            else:
                app.logger.debug("%s's votes did effect the Pareto Front\n",
                                 endorser.username)
                if (len(effect['PF_minus'])):
                    app.logger.debug("Without %s proposals %s "
                                     "would NOT have been on "
                                     "the Pareto Front\n",
                                     endorser.username,
                                     effect['PF_minus'])
                elif (len(effect['PF_plus'])):
                    app.logger.debug("Without %s proposals %s "
                                     "would have been on "
                                     "the Pareto Front\n",
                                     endorser.username,
                                     effect['PF_plus'])

        # '''
        # STOP !!!
        # self.assertTrue(False)

        # Get a list of the current endorsers
        current_endorsers = susans_prop1.endorsers()
        self.assertTrue(type(current_endorsers) is set)
        app.logger.debug("susans_prop1 endorsers = %s\n", current_endorsers)

        current_endorser_ids = susans_prop1.set_of_endorser_ids()
        self.assertEqual(current_endorser_ids, {susan.id, john.id, harry.id})

        endorsements = models.Endorsement.query.filter(
            models.Endorsement.proposal_id == susans_prop1.id).count()
        self.assertEqual(endorsements, 3)
        endorsements = models.Endorsement.query.filter(
            models.Endorsement.proposal_id == bills_prop1.id).count()
        self.assertEqual(endorsements, 2)
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
        # STOP !!!
        #self.assertTrue(False)


class TestWhoDominatesWho(unittest.TestCase):
    def setUp(self):
        setUpDB()

    def tearDown(self):
        tearDownDB()
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


class LoginTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        setUpDB()

    def tearDown(self):
        tearDownDB()
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
        setUpDB()
        self.add_existing_user()

    def tearDown(self):
        tearDownDB()
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
