#!/usr/bin/env python
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
The database Bases
'''

from sqlalchemy import Column, Integer, String, ForeignKey

from sqlalchemy import Enum, DateTime, Text, Boolean, and_

from sqlalchemy.orm import relationship

from database import Base, db_session

import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from flask.ext.login import UserMixin

from . import app


class Update(Base):
    '''
    Stores user question subscription data
    '''

    __tablename__ = 'update'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    how = Column(Enum('daily', 'weekly', 'asap'))
    last_update = Column(DateTime)
    # M:1
    question_id = Column(Integer, ForeignKey('question.id'), primary_key=True)
    subscribed_to = relationship("Question", backref="subscriber_update")

    def __init__(self, subscriber, subscribed_to, how=None):
        self.subscriber = subscriber
        self.subscribed_to = subscribed_to
        self.how = how or 'asap'


class User(Base, UserMixin):
    '''
    Stores the user data
    '''

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True)
    password = Column(String(60), nullable=False)
    registered = Column(DateTime)
    last_seen = Column(DateTime)
    is_active = Column(Boolean, default=True)
    # 1:M
    questions = relationship('Question', backref='author', lazy='dynamic')
    proposals = relationship('Proposal', backref='author', lazy='dynamic',
                             cascade="all, delete-orphan")
    endorsements = relationship('Endorsement',
                                backref='endorser', lazy='dynamic')
    # updates 1:M
    subscribed_questions = relationship("Update", backref='subscriber',
                                        lazy='dynamic',
                                        cascade="all, delete-orphan")
    # invites M:M
    invites = relationship("Invite", primaryjoin="User.id==Invite.sender_id",
                           backref="sender", lazy='dynamic')

    def invite(self, receiver, question):
        # Only author can invite to own question and cannot invite himself
        if (self.id == question.author.id and self.id != receiver.id):
            self.invites.append(Invite(receiver, question.id))
            return True
        return False

    @staticmethod
    def username_available(username):
        return User.query.filter_by(username=username).first() is None

    @staticmethod
    def email_available(email):
        return User.query.filter_by(email=email).first() is None

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.is_active

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def get_endorsed_proposal_ids(self, question, generation=None):
        '''
        .. function:: get_proposals(question[, generation=None])

        Fetch a LIST of the IDs of the proposals endorsed by the
        user for this generation of this question.

        :param question: associated question
        :param generation: question generation
        :type generation: integer or None
        :rtype: list of proposals
        '''
        generation = generation or question.generation

        endorsements = self.endorsements.join(User.endorsements).\
            join(Endorsement.proposal).filter(and_(
                Endorsement.user_id == self.id,
                Proposal.question_id == question.id,
                Endorsement.generation == generation)
            ).all()
        proposal_ids = set()
        for endorsement in endorsements:
            proposal_ids.add(endorsement.proposal_id)
        return proposal_ids

    def get_proposal_ids(self, question, generation=None):
        '''
        .. function:: get_proposals(question[, generation=None])

        Fetch a LIST of the IDs of the proposals authored by the
        user for this question.

        :param question: associated question
        :param generation: question generation
        :type generation: integer or None
        :rtype: list of proposals
        '''
        generation = generation or question.generation
        proposals = self.proposals.filter(and_(
            Proposal.question == question,
            Proposal.generation == generation)
        ).all()
        proposal_ids = list()
        for proposal in proposals:
            proposal_ids.append(proposal.id)
        return proposal_ids

    def get_proposals(self, question, generation=None):
        '''
        .. function:: get_proposals(question[, generation=None])

        Fetch a LIST of the proposals authored by the user for this question.

        :param question: associated question
        :param generation: question generation
        :type generation: integer or None
        :rtype: list of proposals
        '''
        generation = generation or question.generation
        return self.proposals.filter(and_(
            Proposal.question == question,
            Proposal.generation == generation)
        ).all()

    def delete_proposal(self, prop):
        '''
        .. function:: delete_proposal(prop)

        Delete the user's proposal.
        Users can only delete their new proposals during the writing phase
        of the generation in which the proposal is created.

        :param prop: the proposal object to delete
        :rtype: bool
        '''
        proposal = self.proposals.filter(and_(
            Proposal.id == prop.id,
            Proposal.user_id == self.id
        )).first()
        if (proposal is not None
                and proposal.question.phase == 'writing'
                and
                proposal.question.generation == proposal.generation_created):
            self.proposals.remove(proposal)
            return True
        return False

    def subscribe_to(self, question):
        if (question is not None):
            self.subscribed_questions.append(Update(self, question))
        return self

    def unsubscribe_from(self, question):
        if (question is not None):
            subscription = self.subscribed_questions.filter(and_(
                Update.question_id == question.id,
                Update.user_id == self.id)).first()
            if (subscription is not None):
                self.subscribed_questions.remove(subscription)
        return self

    def is_subscribed_to(self, question):
        if (question is not None):
            return self.subscribed_questions.filter(
                Update.question_id == question.id).count() == 1

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
        self.registered = datetime.datetime.utcnow()
        self.last_seen = datetime.datetime.utcnow()

    def __repr__(self):
        return "<User(ID='%s', '%s','%s')>" % (self.id,
                                               self.username,
                                               self.email)


class Invite(Base):
    '''
    Stores users invitaions to participate in questions
    '''

    __tablename__ = 'invite'

    sender_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    receiver_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    question_id = Column(Integer, primary_key=True)

    receiver = relationship("User", primaryjoin="Invite.receiver_id==User.id",
                            backref="invitations", lazy='static')

    def __init__(self, receiver, question_id):
        self.receiver = receiver
        self.question_id = question_id


class Question(Base):
    '''
    Stores question data
    '''

    __tablename__ = 'question'

    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    blurb = Column(Text, nullable=False)
    generation = Column(Integer, default=1, nullable=False)
    room = Column(String(20))
    phase = Column(Enum('writing', 'voting', 'archived'), default='writing')
    created = Column(DateTime)
    last_move_on = Column(DateTime)
    minimum_time = Column(Integer)
    maximum_time = Column(Integer)
    user_id = Column(Integer, ForeignKey('user.id'))
    # 1:M
    proposals = relationship('Proposal', backref='question', lazy='dynamic')
    history = relationship('QuestionHistory', lazy='dynamic')
    key_players = relationship('KeyPlayer', lazy='dynamic')

    def __init__(self, author, title, blurb,
                 minimum_time=86400, maximum_time=604800, room=None):
        self.author = author
        self.title = title
        self.blurb = blurb
        self.room = room or ''
        self.created = datetime.datetime.utcnow()
        self.last_move_on = datetime.datetime.utcnow()
        self.phase = 'writing'
        self.minimum_time = minimum_time
        self.maximum_time = maximum_time

    def save_history(self):
        proposals = self.get_proposals()
        for proposal in proposals:
            self.history.append(QuestionHistory(proposal))
        return self

    def move_to_writing(self):
        if (self.phase not in ['voting', 'archived']
                or not self.minimum_time_passed()):
            return False
        return True

    def get_generation(self, generation):
        return Generation(self, generation)

    def minimum_time_passed(self):
        return (datetime.datetime.utcnow() - self.last_move_on)\
            .total_seconds() > self.minimum_time

    def maximum_time_passed(self):
        return (datetime.datetime.utcnow() - self.last_move_on)\
            .total_seconds() > self.maximum_time

    @staticmethod
    def time_passed_dhm(utc_date_time):
        td = datetime.datetime.utcnow() - utc_date_time
        return {'days': td.days,
                'hours': td.seconds//3600,
                'minutes': (td.seconds//60) % 60}

    @staticmethod
    def time_passed_as_string(utc_date_time):
        time_passed = Question.time_passed_dhm(utc_date_time)
        return "%s days %s hrs %s mins" % (time_passed['days'],
                                           time_passed['hours'],
                                           time_passed['minutes'])

    def change_phase(self, phase=None):
        if (phase is None):
            if (self.phase == 'writing'):
                self.phase = 'voting'
            else:
                self.phase = 'writing'
        else:
            self.phase = phase
        return self

    def get_proposals(self):
        return self.proposals.filter(and_(
            Proposal.question_id == self.id,
            Proposal.generation == self.generation
        )).all()

    def get_proposals_ids(self):
        current_proposals = self.get_proposals()
        prop_ids = set()
        for p in current_proposals:
            prop_ids.add(p.id)
        return prop_ids

    def calculate_pareto_front(self,
                               proposals=None,
                               exclude_user=None,
                               save=False):
        '''
        .. function:: calculate_pareto_front([proposals=None,
                                             exclude_user=None, save=False])

        Calculates the pareto front of the question, and optionally
        saves the dominations in the database.

        :param proposals: list of proposals
        :type proposals: list or boolean
        :param exclude_user: user to exclude from the calculation
        :type exclude_user: User
        :param save: save the domination info in the DB
        :type save: boolean
        :rtype: set of proposal objects
        '''
        proposals = proposals or self.get_proposals()

        if (len(proposals) == 0):
            return set()
        else:
            dominated = set()
            props = dict()

            if (exclude_user is not None):
                app.logger.\
                    debug("calculate_pareto_front called excluding user %s\n",
                          exclude_user.id)

            for p in proposals:
                props[p.id] = p.set_of_endorser_ids()
                if (exclude_user is not None):
                    app.logger.debug("props[p.id] = %s\n", props[p.id])
                    props[p.id].discard(exclude_user.id)
                    app.logger.debug("props[p.id] with user discarded = %s\n",
                                     props[p.id])

            if (exclude_user is not None):
                app.logger.debug("props with %s excluded is now %s\n",
                                 exclude_user.id, props)

            done = list()
            for proposal1 in proposals:
                done.append(proposal1)
                for proposal2 in proposals:
                    if (proposal2 in done):
                        continue

                    who_dominates = Proposal.\
                        who_dominates_who(props[proposal1.id],
                                          props[proposal2.id])

                    if (who_dominates == props[proposal1.id]):
                        dominated.add(proposal2)
                        if (save):
                            app.logger.\
                                debug('SAVE PF: PID %s dominated_by to %s\n',
                                      proposal2.id, proposal1.id)
                            proposal2.dominated_by = proposal1.id
                    elif (who_dominates == props[proposal2.id]):
                        dominated.add(proposal1)
                        if (save):
                            app.logger.\
                                debug('SAVE PF: PID %s dominated_by to %s\n',
                                      proposal2.id, proposal1.id)
                            proposal1.dominated_by = proposal2.id
                        # Proposal 1 dominated, move to next
                        break

            pareto = set()
            if (len(dominated) > 0):
                pareto = set(proposals).difference(dominated)
            else:
                pareto = proposals

            return pareto

    def get_pareto_front(self, calculate_if_missing=False):
        '''
        .. function:: get_pareto_front([calculate_if_missing=False])

        Returns the stored pareto front.
        If no pareto has been saved the pareto is calculated then saved,
        then the newly calculated pareto is returned.

        :param calculate_if_missing: calculate and save the
            domination if missing
        :type calculate_if_missing: boolean
        :rtype: set of proposal objects in the pareto or False.
        '''
        pareto = self.proposals.filter(and_(
            Proposal.question_id == self.question.id,
            Proposal.generation == self.generation,
            Proposal.dominated_by == 0
        )).all()

        # If no pareto saved then calculate pareto, save and return it
        if (len(pareto) == 0):
            if (calculate_if_missing):
                return self.calculate_pareto_front(save=True)
            else:
                return False
        else:
            return pareto

    def get_current_endorsers(self):
        current_endorsers = set()
        all_proposals = self.get_proposals()
        for proposal in all_proposals:
            current_endorsers.update(set(proposal.endorsers()))
        return current_endorsers

    def calculate_key_players(self):
        key_players = dict()
        pareto = self.calculate_pareto_front()
        if (len(pareto) == 0):
            return dict()

        app.logger.debug("+++++++++++ CALCULATE  KEY  PLAYERS ++++++++++\n")
        app.logger.debug("@@@@@@@@@@ PARETO FRONT @@@@@@@@@@ %s\n", pareto)
        current_endorsers = self.get_current_endorsers()
        app.logger.debug("++++++++++ CURRENT ENDORSERS %s\n",
                         current_endorsers)
        for user in current_endorsers:
            app.logger.debug("+++++++++++ Checking User +++++++++++ %s\n",
                             user.id)
            users_endorsed_proposal_ids = set(
                user.get_endorsed_proposal_ids(self))
            app.logger.debug(">>>>>>>>>> Users endorsed proposal IDs %s\n",
                             users_endorsed_proposal_ids)
            app.logger.debug("Calc PF exclusing %s\n", user.id)
            new_pareto = self.calculate_pareto_front(proposals=pareto,
                                                     exclude_user=user)
            app.logger.debug(">>>>>>> NEW PARETO = %s\n", new_pareto)
            if (pareto != new_pareto):
                app.logger.debug("%s is a key player\n", user.id)
                users_pareto_proposals = pareto.difference(new_pareto)
                app.logger.debug(">>>>>>>>>users_pareto_proposals %s\n",
                                 users_pareto_proposals)
                key_players[user.id] = set()
                for users_proposal in users_pareto_proposals:
                    key_players[user.id].update(
                        Question.who_dominates_this_excluding(users_proposal,
                                                              pareto,
                                                              user))
                    app.logger.debug(
                        "Pareto Props that could dominate PID %s %s\n",
                        users_proposal.id,
                        key_players[user.id])
            else:
                app.logger.debug("%s is not a key player\n", user.id)

        self.save_key_players(key_players)
        return key_players

    @staticmethod
    def who_dominates_this_excluding(proposal, pareto, user):
        app.logger.debug("who_dominates_this_excluding\n")
        app.logger.debug(">>>> Pareto %s >>>> User %s\n", pareto, user.id)
        could_dominate = set()
        proposal_endorsers = proposal.set_of_endorser_ids()
        proposal_endorsers = proposal_endorsers.discard(user.id) or set()
        app.logger.debug("Users proposal endorsers (empty?) %s\n",
                         proposal_endorsers)
        for prop in pareto:
            if (prop == proposal):
                continue
            app.logger.debug("Testing Pareto Prop %s for domination\n",
                             prop.id)
            endorsers = prop.set_of_endorser_ids()
            app.logger.debug("Remove %s from %s\n", user.id, endorsers)
            endorsers.discard(user.id)
            app.logger.debug("Current endorsers with user excluded %s\n",
                             endorsers)
            dominated = Proposal.who_dominates_who(proposal_endorsers,
                                                   endorsers)
            app.logger.debug("dominated %s\n", dominated)
            if (dominated == endorsers):
                could_dominate.add(prop)
        return could_dominate

    def save_key_players(self, key_players):
        for user_id in key_players.keys():
            vote_for_these = list(key_players[user_id])
            for vote_for in vote_for_these:
                app.logger.debug("VOTE_FOR %s %s\n",
                                 type(vote_for),
                                 vote_for)
                self.key_players.append(
                    KeyPlayer(user_id,
                              vote_for.id,
                              self.id,
                              self.generation))
        return self

    def calculate_pareto_front_ids(self):
        '''
        .. function:: pareto_front()

        Calculates the pareto front of the question.

        :param generation: question generation
        :type generation: integer or None
        :rtype: set of proposal IDs
        '''
        proposals = self.get_proposals()

        if (len(proposals) == 0):
            return set()
        else:
            dominated = set()
            props = dict()

            for p in proposals:
                props[p.id] = p.set_of_endorser_ids()

            pids = props.keys()
            done = list()
            for proposal1 in pids:
                done.append(proposal1)
                for proposal2 in pids:
                    if (proposal2 in done):
                        continue

                    who_dominates = Proposal.\
                        who_dominates_who(props[proposal1], props[proposal2])
                    if (who_dominates == props[proposal1]):
                        dominated.add(proposal2)
                    elif (who_dominates == props[proposal2]):
                        dominated.add(proposal1)
                        break

            pareto = set()
            if (len(dominated) > 0):
                pareto = set(pids).difference(dominated)

            return pareto

    def __repr__(self):
        return "<Question('%s','%s', '%s')>" % (self.title,
                                                self.author.username,
                                                self.phase)


class Generation():
    question = None
    generation = None

    def proposals(self):
        result = self.question.history.filter(and_(
            QuestionHistory.question_id == self.question.id,
            QuestionHistory.generation == self.generation
        )).all()
        proposals = set()
        for entry in result:
            proposals.add(entry.proposal)
        return proposals

    def pareto_front(self):
        result = self.question.history.filter(and_(
            QuestionHistory.question_id == self.question.id,
            QuestionHistory.generation == self.generation,
            QuestionHistory.dominated_by == 0
        )).all()
        pareto = set()
        for entry in result:
            pareto.add(entry.proposal)
        return pareto

    def endorsers(self):
        pass

    def key_players(self):
        pass

    def __init__(self, question, generation):
        self.question = question
        self.generation = generation

    def __repr__(self):
        return "<Generation(G'%s', Q'%s')>" % (self.generation,
                                               self.question.id)

    def __str__(self):
        return "Generation %s for Question %s" % (self.generation,
                                                  self.question.id)


class KeyPlayer(Base):

    __tablename__ = "key_player"

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    proposal_id = Column(Integer, ForeignKey('proposal.id'), primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id'), primary_key=True)
    generation = Column(Integer, primary_key=True)

    proposal = relationship("Proposal")
    user = relationship("User")
    question = relationship("Question")

    def __init__(self, user_id, proposal_id, question_id, generation):
        self.user_id = user_id
        self.proposal_id = proposal_id
        self.question_id = question_id
        self.generation = generation

    def __repr__(self):
        return "<Generation('%s','%s','%s', '%s')>" % (self.question_id,
                                                       self.proposal_id,
                                                       self.generation,
                                                       self.dominated_by)


class QuestionHistory(Base):
    '''
    Represents the QuestionHistory object which holds the historical
    proposal data for the question.

    Proposal data is copied here when the question is moved on to
    the writing stage.
    '''

    __tablename__ = 'question_history'

    proposal_id = Column(Integer, ForeignKey('proposal.id'), primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id'), primary_key=True)
    generation = Column(Integer, primary_key=True)
    generation_created = Column(Integer)
    dominated_by = Column(Integer)

    proposal = relationship("Proposal")

    def __init__(self, proposal):
        self.proposal_id = proposal.id
        self.question_id = proposal.question_id
        self.generation = proposal.generation
        self.generation_created = proposal.generation_created
        self.dominated_by = proposal.dominated_by

    def __repr__(self):
        return "<Generation('%s','%s','%s', '%s')>" % (self.question_id,
                                                       self.proposal_id,
                                                       self.generation,
                                                       self.dominated_by)


class Proposal(Base):
    '''
    Represents the proposal object
    '''

    __tablename__ = 'proposal'

    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    blurb = Column(Text, nullable=False)
    generation = Column(Integer, default=1)
    generation_created = Column(Integer, default=1)
    created = Column(DateTime)
    updated = Column(DateTime)
    user_id = Column(Integer, ForeignKey('user.id'))
    question_id = Column(Integer, ForeignKey('question.id'))
    dominated_by = Column(Integer, default=0)
    # 1:M
    endorsements = relationship('Endorsement', backref="proposal",
                                lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self, author, question, title, blurb):
        self.author = author
        self.question = question
        self.title = title
        self.blurb = blurb
        self.generation = question.generation
        self.generation_created = question.generation
        self.created = datetime.datetime.utcnow()

    def update(self, user, title, blurb):
        '''
        Only available to the author during the question WRITING PHASE
        of the generation the proposal was first propsosed (created)
        '''
        if (user.id == self.user_id
                and self.question.phase == 'writing'
                and self.question.generation == self.generation_created):
            if (len(title) > 0 and len(blurb) > 0):
                self.title = title
                self.blurb = blurb
                self.updated = datetime.datetime.utcnow()
                return True
        else:
            return False

    def delete(self, user):
        '''
        Only available to the author during the question WRITING PHASE
        of the generation the proposal was first propsosed (created)
        '''
        if (user == self.user_id
                and self.question.phase == 'writing'
                and self.question.generation == self.generation_created):
                    db_session.delete(self)
                    return True
        else:
            return False

    def endorse(self, endorser):
        self.endorsements.append(Endorsement(endorser, self))
        return self

    def remove_endorsement(self, endorser):
        endorsement = self.endorsements.filter(and_(
            Endorsement.user_id == endorser.id,
            Endorsement.proposal_id == self.id,
            Endorsement.generation == self.generation)
        ).first()
        if (endorsement is not None):
            self.endorsements.remove(endorsement)
        return self

    def is_endorsed_by(self, user, generation=None):
        '''
        .. function:: is_endorsed_by(user[, generation=None])

        Check if the user has endorsed this proposal.
        Takes an optional generation value to check historic endorsements.

        :param user: user
        :param generation: question generation
        :type generation: integer or None
        :rtype: bool
        '''
        generation = generation or self.generation

        return self.endorsements.filter(and_(
            Endorsement.user_id == user.id,
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation)
        ).count() == 1

    def endorsers(self, generation=None):
        '''
        Returns a LIST of the current endorsers
            - Defaults to current generation
        '''
        generation = generation or self.generation
        current_endorsements = list()
        current_endorsements = self.endorsements.filter(and_(
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation)
        ).all()
        endorsers = set()
        for e in current_endorsements:
            endorsers.add(e.endorser)
        return endorsers

    def set_of_endorser_ids(self, generation=None):
        '''
        .. function:: set_of_endorser_ids([generation=None])

        Returns the set of user IDs who endorsed this proposal in
        this generation.

        :param generation: proposal generation
        :type generation: integer or None
        :rtype: set of integers
        '''
        endorsers = self.endorsers(generation)
        endorser_ids = set()
        for endorser in endorsers:
            endorser_ids.add(endorser.id)
        return endorser_ids

    @staticmethod
    def who_dominates_who(proposal1, proposal2):
        '''
        .. function:: who_dominates_who(proposal1, proposal2)

        Takes 2 SETS of ENDORSER IDs representing who endorsed each proposal
        and calulates which proposal if any domiantes the other.
        Returns either the dominating set, or an integer value of:
            0 if the sets of endorsers are different
            -1 if the sets of endorsers are the same

        :param proposal1: set of voters for proposal 1
        :param proposal2: set of voters for proposal 2
        :param generation: question generation
        :type proposal1: set of integers
        :type proposal2: set of integers
        :rtype: interger or set of integers
        '''
        # If proposal1 and proposal2 are the same return -1
        if (proposal1 == proposal2):
            return -1
        # If proposal1 is empty return proposal2
        elif (len(proposal1) == 0):
            return proposal2
        # If proposal2 is empty return proposal1
        elif (len(proposal2) == 0):
            return proposal1
        # Check if proposal1 is a propoer subset of proposal2
        elif (proposal1 < proposal2):
            return proposal2
        # Check if proposal2 is a proper subset of proposal1
        elif (proposal2 < proposal1):
            return proposal1
        # proposal1 and proposal2 are different return 0
        else:
            return 0

    def __repr__(self):
        return "<Proposal('%s', '%s','%s', '%s', dominated_by '%s')>"\
            % (self.id,
               self.title,
               self.blurb,
               self.question_id,
               self.dominated_by)


class Endorsement(Base):
    '''
    Stores endorsement data
    '''

    __tablename__ = 'endorsement'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    proposal_id = Column(Integer, ForeignKey('proposal.id'))
    generation = Column(Integer, nullable=False)
    endorsement_date = Column(DateTime)

    def __init__(self, endorser, proposal):
        self.endorser = endorser
        self.proposal = proposal
        self.generation = proposal.generation
        self.endorsement_date = datetime.datetime.utcnow()
