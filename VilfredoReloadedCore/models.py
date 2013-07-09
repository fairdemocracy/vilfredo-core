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

from sqlalchemy import Enum, DateTime, Text, and_, event

from sqlalchemy.orm import relationship, backref

from database import Base, db_session

import datetime

import copy

from werkzeug.security import check_password_hash, generate_password_hash

from flask.ext.login import UserMixin

from . import app

from HTMLParser import HTMLParser


def enum(**enums):
    return type('Enum', (), enums)


GraphLevelType = enum(layers=1, num_votes=2, flat=3)


class Update(Base):
    '''
    Stores user question subscription data
    '''

    __tablename__ = 'update'

    user_id = Column(Integer, ForeignKey('user.id'),
                     primary_key=True, autoincrement=False)
    how = Column(Enum('daily', 'weekly', 'asap'))
    last_update = Column(DateTime)
    # M:1
    question_id = Column(Integer, ForeignKey('question.id'),
                         primary_key=True, autoincrement=False)

    subscribed_to = relationship("Question", backref="subscriber_update",
                                 cascade="all, delete-orphan",
                                 single_parent=True)

    def __init__(self, subscriber, subscribed_to, how=None):
        self.user_id = subscriber.id
        self.question_id = subscribed_to.id
        self.how = how or 'asap'


class User(Base, UserMixin):
    '''
    Stores the user data
    '''

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120))
    password = Column(String(60), nullable=False)
    registered = Column(DateTime)
    last_seen = Column(DateTime)
    # 1:M
    questions = relationship('Question', backref='author', lazy='dynamic',
                             cascade="all, delete-orphan")

    proposals = relationship('Proposal', backref='author', lazy='dynamic',
                             cascade="all, delete-orphan")

    endorsements = relationship('Endorsement',
                                backref='endorser', lazy='dynamic',
                                cascade="all, delete-orphan")

    # updates 1:M
    subscribed_questions = relationship("Update", backref='subscriber',
                                        lazy='dynamic',
                                        cascade="all, delete-orphan")

    # invites M:M
    invites = relationship("Invite", primaryjoin="User.id==Invite.sender_id",
                           backref="sender", lazy='dynamic',
                           cascade="all, delete-orphan")

    def invite(self, receiver, question):
        # Only author can invite to own question and cannot invite himself
        '''
        .. function:: invite(receiver, question)

        Create an invitation to request the receiver participate
        in the question.

        :param receiver: the user to be invited
        :type receiver: User
        :param question: the author's question
        :type question: Question
        :rtype: boolean
        '''
        if (self.id == question.author.id and self.id != receiver.id):
            self.invites.append(Invite(self, receiver, question.id))
            return True
        return False

    @staticmethod
    def username_available(username):
        '''
        .. function:: username_available(username)

        Checks if an email username is available.

        :param email: username
        :type email: string
        :rtype: boolean
        '''
        return User.query.filter_by(username=username).first() is None

    @staticmethod
    def email_available(email):
        '''
        .. function:: email_available(email)

        Checks if an email address is available.

        :param email: email address
        :type email: string
        :rtype: boolean
        '''
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
        .. function:: get_endorsed_proposal_ids(question[, generation=None])

        Fetch a set of the IDs of the proposals endorsed by the
        user for this generation of this question.

        :param question: associated question
        :type question: Question
        :param generation: question generation
        :type generation: integer or None
        :rtype: set
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

    def get_endorsed_proposals(self, question, generation=None):
        '''
        .. function:: get_endorsed_proposals(question[, generation=None])

        Fetch a LIST of the proposals endorsed by the
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
        proposals = set()
        for endorsement in endorsements:
            proposals.add(endorsement.proposal)
        return proposals

    def get_endorsments(self, question, generation=None):
        '''
        .. function:: get_endorsments(question[, generation=None])

        Fetch a LIST of the IDs of the proposals endorsed by the
        user for this generation of this question.

        :param question: associated question
        :param generation: question generation
        :type generation: integer or None
        :rtype: list of proposals
        '''
        generation = generation or question.generation

        return self.endorsements.join(User.endorsements).\
            join(Endorsement.proposal).filter(and_(
                Endorsement.user_id == self.id,
                Proposal.question_id == question.id,
                Endorsement.generation == generation)
            ).all()

    def get_proposal_ids(self, question, generation=None):
        '''
        .. function:: get_proposal_ids(question[, generation=None])

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
        '''
        return self.proposals.filter(and_(
            Proposal.question == question,
            Proposal.generation == generation)
        ).all()
        '''
        return db_session.query(Proposal).join(QuestionHistory).\
            filter(QuestionHistory.question_id == question.id).\
            filter(QuestionHistory.generation == generation).\
            all()

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

            # Delete entry from QuestionHistory table or not ???
            self.proposals.remove(proposal)
            return True
        return False

    def subscribe_to(self, question, how=None):
        '''
        .. function:: subscribe_to(question[, how])

        Subscribe the user to the question.

        :param question: the question to subscribe to.
        :type question: Question
        :param how: the author's question
        :type question: enum 'daily', 'weekly', 'asap'
        '''
        if (question is not None):
            self.subscribed_questions.append(Update(self, question, how))
        return self

    def unsubscribe_from(self, question):
        '''
        .. function:: unsubscribe_from(question)

        Unsubscribe the user from the question.

        :param question: the question to subscribe to.
        :type question: Question
        '''
        if (question is not None):
            subscription = self.subscribed_questions.filter(and_(
                Update.question_id == question.id,
                Update.user_id == self.id)).first()
            if (subscription is not None):
                self.subscribed_questions.remove(subscription)
        return self

    def is_subscribed_to(self, question):
        '''
        .. function:: is_subscribed_to(question)

        Checks if the user issubscribed to the question.

        :param question: the question to subscribe to.
        :type question: Question
        :rtype: boolean
        '''
        if (question is not None):
            return self.subscribed_questions.filter(
                Update.question_id == question.id).count() == 1

    def set_password(self, password):
        '''
        .. function:: set_password(password)

        Hashes the password and stores it in the database.

        :param password: the user's password.
        :type password: string
        '''
        self.password = generate_password_hash(password)

    def check_password(self, password):
        '''
        .. function:: check_password(password)

        Checks the user's password against the hashed string stored
        in the database.

        :param password: the user's password to check.
        :type password: string
        :rtype: boolean
        '''
        return check_password_hash(self.password, password)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
        self.registered = datetime.datetime.utcnow()
        self.last_seen = datetime.datetime.utcnow()

    def __repr__(self):
        return "<User(ID='%s', '%s')>" % (self.id,
                                          self.username)


class Invite(Base):
    '''
    Stores users invitaions to participate in questions
    '''
    __tablename__ = 'invite'

    sender_id = Column(Integer, ForeignKey('user.id'),
                       primary_key=True, autoincrement=False)
    receiver_id = Column(Integer, ForeignKey('user.id'),
                         primary_key=True, autoincrement=False)
    question_id = Column(Integer, primary_key=True, autoincrement=False)

    receiver = relationship("User", primaryjoin="Invite.receiver_id==User.id",
                            backref="invitations",
                            lazy='static', single_parent=True,
                            cascade="all, delete-orphan")

    def __init__(self, sender, receiver, question_id):
        self.sender_id = sender.id
        self.receiver_id = receiver.id
        self.question_id = question_id


class Question(Base):
    '''
    Stores data and handles functionality and relations for
    the question object.
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
    proposals = relationship('Proposal', backref='question', lazy='dynamic',
                             cascade="all, delete-orphan")
    history = relationship('QuestionHistory', lazy='dynamic',
                           cascade="all, delete-orphan")
    key_players = relationship('KeyPlayer', lazy='dynamic',
                               cascade="all, delete-orphan")

    def __init__(self, author, title, blurb,
                 minimum_time=86400, maximum_time=604800, room=None):
        '''
        .. function:: __init__(author, title, blurb
                [, minimum_time=86400, maximum_time=604800, room=None])

        Creates a Question object.

        :param author: author of the question
        :type author: User
        :param title: author of the question
        :type title: string
        :param blurb: author of the question
        :type blurb: string
        :param minimum_time: author of the question
        :type minimum_time: integer
        :param maximum_time: author of the question
        :type maximum_time: integer
        :param room: room associated with the question
        :type room: string
        '''
        self.user_id = author.id
        self.title = title
        self.blurb = blurb
        self.room = room or ''
        self.created = datetime.datetime.utcnow()
        self.last_move_on = datetime.datetime.utcnow()
        self.phase = 'writing'
        self.minimum_time = minimum_time
        self.maximum_time = maximum_time

    def save_history(self):
        '''
        .. function:: save_history()

        Saves the current state of the question to the question_history table.

        :rtype: boolean
        '''
        proposals = self.get_proposals()
        for proposal in proposals:
            self.history.append(QuestionHistory(proposal))
        return self

    def move_to_writing(self):
        '''
        .. function:: move_to_writing()

        Moves the question to the writing phase if the minimum time has
        passed and and the question is currently voting or archived.

        :rtype: boolean
        '''
        if (self.phase not in ['voting', 'archived']
                or not self.minimum_time_passed()):
            return False
        return True

    def get_generation(self, generation=None):
        '''
        .. function:: get_generation(generation)

        Returns a Generation object for the question.

        :rtype: Generation
        '''
        return Generation(self, generation)

    def minimum_time_passed(self):
        '''
        .. function:: minimum_time_passed()

        Returns True if the minimum time has passed for the question.

        :rtype: boolean
        '''
        return (datetime.datetime.utcnow() - self.last_move_on)\
            .total_seconds() > self.minimum_time

    def maximum_time_passed(self):
        '''
        .. function:: maximum_time_passed()

        Returns True if the maximum time has passed for the question.

        :rtype: boolean
        '''
        return (datetime.datetime.utcnow() - self.last_move_on)\
            .total_seconds() > self.maximum_time

    @staticmethod
    def time_passed_dhm(utc_date_time):
        '''
        .. function:: time_passed_dhm(utc_date_time)

        Returns the time passed in days, hours and minutes since utc_date_time.

        :param utc_date_time: a time in the past.
        :type utc_date_time: DateTime
        :rtype: dict
        '''
        td = datetime.datetime.utcnow() - utc_date_time
        return {'days': td.days,
                'hours': td.seconds//3600,
                'minutes': (td.seconds//60) % 60}

    @staticmethod
    def time_passed_as_string(utc_date_time):
        '''
        .. function:: time_passed_as_string(utc_date_time)

        Returns a formatted string of the time passed in days, hours
        and minutes since utc_date_time.

        :param utc_date_time: a time in the past.
        :type utc_date_time: DateTime
        :rtype: string
        '''
        time_passed = Question.time_passed_dhm(utc_date_time)
        return "%s days %s hrs %s mins" % (time_passed['days'],
                                           time_passed['hours'],
                                           time_passed['minutes'])

    def change_phase(self, phase=None):
        '''
        .. function:: change_phase([phase])

        Returns a formatted string of the time passed in days, hours
        and minutes since utc_date_time.

        :param phase: the phase to set the question to.
        :type phase: string
        '''
        if (phase is None):
            if (self.phase == 'writing'):
                self.phase = 'voting'
            else:
                self.phase = 'writing'
        else:
            self.phase = phase
        return self

    def get_proposal_info(self, generation=None):
        '''
        .. function:: get_proposal_info([generation=None])

        Returns a list of history entries and their related proposals
        for the selected generation of the question.

        :param generation: question generation.
        :type generation: integer
        :rtype: list
        '''
        generation = generation or self.generation

        return db_session.query(Proposal, QuestionHistory).\
            filter(Proposal.id == QuestionHistory.proposal_id).\
            filter(QuestionHistory.question_id == self.id).\
            filter(QuestionHistory.generation == generation).\
            all()

    def get_history(self, generation=None):
        '''
        .. function:: get_history([generation=None])

        Returns a dictionary of histroy entries for that generation
        of this question indexed by the peoposal ID.

        :param generation: question generation.
        :type generation: integer
        :rtype: dict
        '''
        generation = generation or self.generation

        history = db_session.query(QuestionHistory).\
            filter(QuestionHistory.question_id == self.id).\
            filter(QuestionHistory.generation == generation).\
            all()

        history_data = dict()
        for entry in history:
            history_data[entry.proposal_id] = entry
        return history_data

    def get_proposals(self, generation=None):
        '''
        .. function:: get_proposals()

        Returns a set of proposals for the current generation of
        the question.

        :param generation: question generation.
        :type generation: integer
        :rtype: set
        '''
        generation = generation or self.generation

        proposals = db_session.query(Proposal).join(QuestionHistory).\
            filter(QuestionHistory.question_id == self.id).\
            filter(QuestionHistory.generation == generation).\
            all()
        return set(proposals)

    def get_proposal_ids(self, generation=None):
        '''
        .. function:: get_proposal_ids([generation=None])

        Returns a set of proposal IDs for the current generation of
        the question.

        :param generation: question generation.
        :type generation: integer
        :rtype: set
        '''
        generation = generation or self.generation
        ids = set()
        props = db_session.query(QuestionHistory).\
            filter(QuestionHistory.question_id == self.id).\
            filter(QuestionHistory.generation == generation).\
            all()
        for prop in props:
            ids.add(prop.proposal_id)
        return ids

    def calculate_element_relations(self, elements, generation=None):
        '''
        .. function:: calculate_relations([generation=None])

        Calculates the complete map of dominations between elements. For each
        element it calculates which dominates and which are dominated.

        :param generation: question generation.
        :type generation: integer
        :rtype: dict
        '''
        generation = generation or self.generation

        all_relations = dict()
        props = dict()
        all_elements = self.get_proposals(generation)
        for p in all_elements:
            props[p.id] = p.set_of_endorser_ids(generation)

        for element1 in all_elements:
            dominating = set()
            dominated = set()
            all_relations[element1] = dict()

            for element2 in all_elements:
                if (element1 == element2):
                    continue
                who_dominates = Question.\
                    which_element_dominates_which(props[element1.id],
                                                  props[element2.id])

                app.logger.debug("Comparing props %s %s and %s %s\n",
                                 element1.id, props[element1.id],
                                 element2.id, props[element2.id])
                app.logger.debug("   ===> WDW Result = %s\n",
                                 who_dominates)

                if (who_dominates == props[element1.id]):
                    dominating.add(element2)
                elif (who_dominates == props[element2.id]):
                    dominated.add(element2)

            all_relations[element1]['dominating'] = dominating
            all_relations[element1]['dominated'] = dominated

        return all_relations

    @staticmethod
    def which_element_dominates_which(element1, element2):
        '''
        .. function:: who_dominateselement_who(element1, element2)

        Takes 2 SETS and calulates which element if any
        domiantes the other.
        Returns either the dominating set, or an integer value of:
            0 if the sets of endorsers are different
            -1 if the sets of endorsers are the same

        :param element1: element 1
        :type element1: set of integers
        :param element2: element 2
        :type element2: set of integers
        :rtype: interger or set of integers
        '''
        # If element1 and element2 are the same return -1
        if (element1 == element2):
            return -1
        # If element1 is empty return element2
        elif (len(element1) == 0):
            return element2
        # If element2 is empty return element1
        elif (len(element2) == 0):
            return element1
        # Check if element1 is a propoer subset of element2
        elif (element1 < element2):
            return element2
        # Check if element2 is a proper subset of element1
        elif (element2 < element1):
            return element1
        # element1 and element2 are different return 0
        else:
            return 0

    def calculate_endorser_relations(self, generation=None):
        '''
        .. function:: calculate_endorser_relations([generation=None])

        Calculates the complete map of dominations. For each endorser
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: integer
        :rtype: dict
        '''
        generation = generation or self.generation

        endorser_relations = dict()
        endorsements = dict()
        all_endorsers = self.get_endorsers(generation)
        for e in all_endorsers:
            endorsements[e.id] = e.get_endorsed_proposal_ids(self, generation)

        for endorser1 in all_endorsers:
            dominating = set()
            dominated = set()
            endorser_relations[endorser1] = dict()

            for endorser2 in all_endorsers:
                if (endorser1 == endorser2):
                    continue
                who_dominates = Question.\
                    which_element_dominates_which(endorsements[endorser1.id],
                                                  endorsements[endorser2.id])

                app.logger.debug("Comparing endorsements %s %s and %s %s\n",
                                 endorser1.id, endorsements[endorser1.id],
                                 endorser2.id, endorsements[endorser2.id])
                app.logger.debug("   ===> WDW Result = %s\n",
                                 who_dominates)

                if (who_dominates == endorsements[endorser1.id]):
                    dominating.add(endorser2)
                elif (who_dominates == endorsements[endorser2.id]):
                    dominated.add(endorser2)

            endorser_relations[endorser1]['dominating'] = dominating
            endorser_relations[endorser1]['dominated'] = dominated

        return endorser_relations

    def calculate_proposal_relations(self, generation=None):
        '''
        .. function:: calculate_proposal_relations([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: integer
        :rtype: dict
        '''
        generation = generation or self.generation

        proposal_relations = dict()
        props = dict()
        all_proposals = self.get_proposals(generation)
        for p in all_proposals:
            props[p.id] = p.set_of_endorser_ids(generation)

        for proposal1 in all_proposals:
            dominating = set()
            dominated = set()
            proposal_relations[proposal1] = dict()

            for proposal2 in all_proposals:
                if (proposal1 == proposal2):
                    continue
                who_dominates = Proposal.\
                    who_dominates_who(props[proposal1.id],
                                      props[proposal2.id])

                app.logger.debug("Comparing props %s %s and %s %s\n",
                                 proposal1.id, props[proposal1.id],
                                 proposal2.id, props[proposal2.id])
                app.logger.debug("   ===> WDW Result = %s\n",
                                 who_dominates)

                if (who_dominates == props[proposal1.id]):
                    dominating.add(proposal2)
                elif (who_dominates == props[proposal2.id]):
                    dominated.add(proposal2)

            proposal_relations[proposal1]['dominating'] = dominating
            proposal_relations[proposal1]['dominated'] = dominated

        return proposal_relations

    def calculate_pareto_front(self,
                               proposals=None,
                               exclude_user=None,
                               generation=None,
                               save=False):
        '''
        .. function:: calculate_pareto_front([proposals=None,
                                             exclude_user=None,
                                             generation=None,
                                             save=False])

        Calculates the pareto front of the question, and optionally
        saves the dominations in the database.

        :param proposals: list of proposals
        :type proposals: list or boolean
        :param exclude_user: user to exclude from the calculation
        :type exclude_user: User
        :param generation: question generation.
        :type generation: integer
        :param save: save the domination info in the DB
        :type save: boolean
        :rtype: set of proposal objects
        '''
        generation = generation or self.generation
        proposals = proposals or self.get_proposals(generation)
        history = self.get_history()

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
                props[p.id] = p.set_of_endorser_ids(generation)
                if (exclude_user is not None):
                    app.logger.debug("props[p.id] = %s\n", props[p.id])
                    props[p.id].discard(exclude_user.id)
                    app.logger.debug("props[p.id] with user %s "
                                     "discarded = %s\n",
                                     exclude_user.id,
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
                            history[proposal2.id].dominated_by = proposal1.id
                    elif (who_dominates == props[proposal2.id]):
                        dominated.add(proposal1)
                        if (save):
                            app.logger.\
                                debug('SAVE PF: PID %s dominated_by to %s\n',
                                      proposal2.id, proposal1.id)
                            history[proposal1.id].dominated_by = proposal2.id
                        # Proposal 1 dominated, move to next
                        break

            pareto = set()
            if (len(dominated) > 0):
                pareto = set(proposals).difference(dominated)
            else:
                pareto = set(proposals)

            return pareto

    def calculate_pareto_front_ids(self, generation=None):
        '''
        .. function:: calculate_pareto_front_ids([generation=None])

        Returns the IDs of the stored pareto front.
        If no pareto has been saved the pareto is calculated then saved,
        then the set of IDs of the newly calculated pareto is returned.

        :param generation: question generation.
        :type generation: integer
        :rtype: set or boolean.
        '''
        generation = generation or self.generation
        pareto = self.calculate_pareto_front(generation=generation)
        # pareto = self.get_pareto_front(calculate_if_missing=True,
        #                                generation=generation)
        pareto_ids = set()
        for proposal in pareto:
            pareto_ids.add(proposal.id)
        return pareto_ids

    def get_pareto_front(self, calculate_if_missing=False, generation=None):
        '''
        .. function:: get_pareto_front([calculate_if_missing=False,
                                        generation=None])

        Returns the stored pareto front.
        If no pareto has been saved the pareto is calculated then saved,
        then the newly calculated pareto is returned.

        :param calculate_if_missing: calculate and save the
            domination if missing
        :type calculate_if_missing: boolean
        :param generation: question generation.
        :type generation: integer
        :rtype: set or boolean.
        '''
        generation = generation or self.generation

        pareto = db_session.query(Proposal).join(QuestionHistory).\
            filter(QuestionHistory.question_id == self.id).\
            filter(QuestionHistory.generation == generation).\
            filter(QuestionHistory.dominated_by == 0).\
            all()

        # If no pareto saved then calculate pareto, save and return it
        if (len(pareto) == 0):
            if (calculate_if_missing):
                return self.calculate_pareto_front(
                    generation=generation,
                    save=True)
            else:
                return False
        else:
            return pareto

    def get_endorsers(self, generation=None):
        '''
        .. function:: get_endorsers([generation=None])

        Returns a set of endorsers for the current generation of
        the question.

        :param generation: question generation.
        :type generation: integer
        :rtype: set
        '''
        generation = generation or self.generation

        current_endorsers = set()
        all_proposals = self.get_proposals(generation)
        for proposal in all_proposals:
            current_endorsers.update(set(proposal.endorsers(generation)))
        return current_endorsers

    def calculate_endorser_effects(self, generation=None):
        '''
        .. function:: calculate_endorser_effects([generation=None])

        Calculates the effects each endorser has on the pareto.
        What would be the effects if he didn't vote?
        What proposals has he forced into the pareto?

        :param generation: question generation.
        :type generation: integer
        :rtype: dict
        '''
        generation = generation or self.generation

        all_endorsers = self.get_endorsers(generation)
        app.logger.debug("All Endorsers: %s\n", all_endorsers)
        pareto = self.calculate_pareto_front(generation=generation)
        endorser_effects = dict()
        for endorser in all_endorsers:
            PF_excluding_endorser = self.calculate_pareto_front(
                exclude_user=endorser,
                generation=generation)
            PF_plus = PF_excluding_endorser - pareto
            PF_minus = pareto - PF_excluding_endorser
            if (len(PF_plus) or len(PF_minus)):
                endorser_effects[endorser] = {
                    'PF_excluding': PF_excluding_endorser,
                    'PF_plus': PF_plus,
                    'PF_minus': PF_minus}
            else:
                endorser_effects[endorser] = None
        return endorser_effects

    def calculate_key_players(self, generation=None):
        '''
        .. function:: calculate_key_players([generation=None])

        Calculates the effects each endorser has on the pareto.
        What would be the effects if he didn't vote?
        What proposals has he forced into the pareto?

        :param generation: question generation.
        :type generation: integer
        :rtype: dict
        '''
        generation = generation or self.generation

        key_players = dict()
        pareto = self.calculate_pareto_front(generation=generation)
        if (len(pareto) == 0):
            return dict()

        app.logger.debug("+++++++++++ CALCULATE  KEY  PLAYERS ++++++++++\n")
        app.logger.debug("@@@@@@@@@@ PARETO FRONT @@@@@@@@@@ %s\n", pareto)
        current_endorsers = self.get_endorsers(generation)
        app.logger.debug("++++++++++ CURRENT ENDORSERS %s\n",
                         current_endorsers)
        for user in current_endorsers:
            app.logger.debug("+++++++++++ Checking User +++++++++++ %s\n",
                             user.id)
            users_endorsed_proposal_ids =\
                user.get_endorsed_proposal_ids(self, generation)
            app.logger.debug(">>>>>>>>>> Users endorsed proposal IDs %s\n",
                             users_endorsed_proposal_ids)
            app.logger.debug("Calc PF excluding %s\n", user.id)
            new_pareto = self.calculate_pareto_front(proposals=pareto,
                                                     exclude_user=user,
                                                     generation=generation)
            app.logger.debug(">>>>>>> NEW PARETO = %s\n", new_pareto)
            if (pareto != new_pareto):
                app.logger.debug("%s is a key player\n", user.id)
                users_pareto_proposals = pareto.difference(new_pareto)
                app.logger.debug(">>>>>>>>>users_pareto_proposals %s\n",
                                 users_pareto_proposals)
                key_players[user.id] = set()
                for users_proposal in users_pareto_proposals:
                    key_players[user.id].update(
                        Question.who_dominates_this_excluding(
                            users_proposal,
                            pareto,
                            user,
                            generation))
                    app.logger.debug(
                        "Pareto Props that could dominate PID %s %s\n",
                        users_proposal.id,
                        key_players[user.id])
            else:
                app.logger.debug("%s is not a key player\n", user.id)

        # self.save_key_players(key_players)
        app.logger.debug("Question.calc_key_players: %s", key_players)
        return key_players

    @staticmethod
    def who_dominates_this_excluding(proposal, pareto, user, generation=None):
        '''
        .. function:: who_dominates_this_excluding(proposal, pareto,
                                                   user[, generation])

        Calculates the set of proposals within the pareto which could dominate
        the proposal if the endorsements of the user were excluded from the
        calculation.

        :param proposal: calculate and save the
        :type proposal: Proposal object
        :param pareto: the pareto front
        :type pareto: set
        :param user: the user to exclude from the calculation
        :type user: User
        :param generation: the generation
        :type generation: integer or None
        :rtype: set
        '''

        app.logger.debug("who_dominates_this_excluding\n")
        app.logger.debug(">>>> Pareto %s >>>> User %s\n", pareto, user.id)
        could_dominate = set()
        proposal_endorsers = proposal.set_of_endorser_ids(generation)
        proposal_endorsers.discard(user.id)
        app.logger.debug("Users proposal %s endorsers %s\n",
                         proposal.id,
                         proposal_endorsers)
        for prop in pareto:
            if (prop == proposal):
                continue
            app.logger.debug("Testing Pareto Prop %s for domination\n",
                             prop.id)
            endorsers = prop.set_of_endorser_ids(generation)
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
        '''
        .. function:: save_key_players(key_players)

        Saves the key player data to the database.

        :param key_players: the key players
        :type key_players: dict
        '''
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

    def invert_dict(d):
        inv = dict()
        for k, v in d.iteritems():
            keys = inv.setdefault(v, set())
            keys.append(k)
        return inv

    def make_graphviz_map(self,
                          proposals=None,
                          generation=None,
                          internal_links=False,
                          proposal_level_type=GraphLevelType.layers,
                          user_level_type=GraphLevelType.layers,
                          address_image='',
                          highlight_user1=None,
                          highlight_proposal1=None):
        '''
        .. function:: make_graphviz_map(
            [proposals=None,
            generation=None,
            internal_links=False,
            proposal_level_type=GraphLevelType.layers,
            user_level_type=GraphLevelType.layerss,
            address_image='',
            highlight_user1=None,
            highlight_proposal1=None])

        Generates the string to create a voting graph from Graphviz.

        :param proposals: set of proposals
        :type generation: set or None
        :param generation: the generation
        :type generation: integer or None
        :param internal_links:
        :type internal_links: boolean or None
        :param proposal_level_type: required layout of user nodes
        :type proposal_level_type: GraphLevelType
        :param user_level_type: required layout of user nodes
        :type user_level_type: GraphLevelType
        :param address_image: url of the map
        :type address_image: string
        :param highlight_user1: Proposal to highlight
        :type highlight_user1: string
        :param highlight_proposal1: User to highlight
        :type highlight_proposal1: string
        :rtype: string
        '''
        generation = generation or self.generation

        # get set of all proposals
        proposals = proposals or self.get_proposals(generation)
        app.logger.debug("all proposals %s\n",
                         proposals)

        # get pareto
        pareto = self.calculate_pareto_front(proposals=proposals,
                                             generation=generation)
        app.logger.debug("pareto %s\n",
                         pareto)

        # get set of all endorsers
        # endorsers = self.get_endorsers(generation)
        endorsers = set()
        for proposal in proposals:
            endorsers.update(proposal.endorsers(generation))
        app.logger.debug("endorsers %s\n",
                         endorsers)

        # get dict of all proposals => endorsers
        proposal_endorsers = dict()
        for proposal in proposals:
            proposal_endorsers[proposal] =\
                proposal.endorsers(generation)
        app.logger.debug("proposal_endorsers %s\n",
                         proposal_endorsers)

        # get dict of all endorsers => proposals
        endorser_proposals = dict()
        for endorser in endorsers:
            endorser_proposals[endorser] =\
                endorser.get_endorsed_proposal_ids(self, generation)
        app.logger.debug("endorser_proposals %s\n",
                         endorser_proposals)

        # get dict of pareto proposals => endorsers
        pareto_endorsers = dict()
        for proposal in pareto:
            pareto_endorsers[proposal.id] = proposal.endorsers(generation)
        app.logger.debug("pareto proposals => endorsers %s\n",
                         pareto_endorsers)

        proposal_relations = self.calculate_proposal_relations(generation)
        app.logger.debug("proposal_relations %s\n",
                         proposal_relations)

        proposals_below = dict()
        proposals_above = dict()
        for (proposal, relation) in proposal_relations.iteritems():
            proposals_below[proposal] = relation['dominating']
            proposals_above[proposal] = relation['dominated']
        app.logger.debug("proposals_below %s\n",
                         proposals_below)
        app.logger.debug("proposals_above %s\n",
                         proposals_above)

        proposals_covered = self.get_covered(proposals_below, proposals)
        app.logger.debug("proposals_covered %s\n",
                         proposals_covered)

        # Endorser relations
        endorser_relations = self.calculate_endorser_relations(generation)
        app.logger.debug("endorser_relations %s\n",
                         endorser_relations)

        endorsers_below = dict()
        endorsers_above = dict()
        for (endorser, relation) in endorser_relations.iteritems():
            endorsers_below[endorser] = relation['dominating']
            endorsers_above[endorser] = relation['dominated']
        app.logger.debug("endorsers_below %s\n",
                         endorsers_below)
        app.logger.debug("endorsers_above %s\n",
                         endorsers_above)

        endorsers_covered = self.get_covered(endorsers_below, endorsers)
        app.logger.debug("endorsers_covered %s\n",
                         endorsers_covered)

        endorsers_covering = self.get_covered(endorsers_above, endorsers)
        app.logger.debug("endorsers_covering %s\n",
                         endorsers_covering)

        if (proposal_level_type == GraphLevelType. num_votes):
            proposal_levels = self.find_levels_based_on_size(
                proposal_endorsers)
        elif (proposal_level_type == GraphLevelType.layers):
            proposal_levels = self.find_levels(proposals_covered, proposals)
        else:
            proposal_levels = list()
            proposal_levels[0] = proposals

        app.logger.debug("proposal_levels %s\n",
                         proposal_levels)

        if (user_level_type == GraphLevelType. num_votes):
            user_levels = self.find_levels_based_on_size(endorser_proposals)
                # reverse()
        elif (user_level_type == GraphLevelType.layers):
            user_levels = self.find_levels(endorsers_covering, endorsers)
        # elif (user_level_type == "flat"):
        else:
            user_levels = list()
            user_levels[0] = endorsers

        app.logger.debug("user_levels %s\n",
                         user_levels)

        combined_proposals = self.combine_proposals(
            proposal_endorsers, proposals)

        app.logger.debug("proposal_endorsers A %s\n",
                         proposal_endorsers)

        bundled_proposals = set()
        for (proposal, relations) in combined_proposals.iteritems():
            bundled_proposals.update(relations)
            relations.add(proposal)

        app.logger.debug("combined_proposals %s\n",
                         combined_proposals)
        app.logger.debug("bundled_proposals %s\n",
                         bundled_proposals)

        combined_users = self.combine_users(
            proposal_endorsers, endorsers, generation)

        bundled_users = set()
        for (endorser, relations) in combined_users.iteritems():
            bundled_users.update(relations)
            relations.append(endorser)

        app.logger.debug("combined_users %s\n",
                         combined_users)
        app.logger.debug("bundled_users %s\n",
                         bundled_users)

        proposal_levels_keys = proposal_levels.keys()
        user_levels_keys = user_levels.keys()

        if (proposal_level_type == "num_votes"):
            full_size_note = max(proposal_levels_keys)
        else:
            # default to "layers"
            full_size_note = 0

        all_graphs_note = max(user_levels_keys)

        # Begin creation of Graphviz string
        title = self.string_safe(self.title)
        voting_graph = 'digraph "%s" {\n' % (title)

        for l in proposal_levels_keys:
            if (l == full_size_note):
                voting_graph += ' "pl' + str(full_size_note) +\
                    '" [label="Full\\nSize" shape=circle style=filled ' +\
                    'color=Black peripheries=1 fillcolor=palegoldenrod ' +\
                    'tooltip="Look at this image in full size"' +\
                    ' fontsize=10 URL="' + address_image +\
                    '" target="_top" width=.75 height=.75 ]; \n'
            else:
                voting_graph += ' "pl' + str(l) +\
                    '" [shape=point fontcolor=white ' +\
                    'color=white fontsize=1]; \n'

        for l in user_levels_keys:
            if (l == all_graphs_note):
                all_graph_url = 'http://view_gen.html'
                voting_graph += ' "ul' + str(all_graphs_note) +\
                    '" [label="All\\nGraphs" ' +\
                    'shape=circle style=filled color=Black ' +\
                    'peripheries=1  ' +\
                    'fillcolor=palegoldenrod ' +\
                    'tooltip="Look at all the ' +\
                    'alternative views of this information" ' +\
                    'fontsize=9 URL="' +\
                    all_graph_url + '" target="_top" width=.75 ' +\
                    'height=.75 ]; \n'
            else:
                voting_graph += ' "ul' + str(l) + '" [shape=point ' +\
                    'fontcolor=white ' +\
                    'color=white fontsize=1]; \n'

        for l in proposal_levels_keys:
            if (l != proposal_levels_keys[0]):
                voting_graph += ' -> '
            voting_graph += '"pl' + str(l) + '" '

        for l in user_levels_keys:
            voting_graph += ' -> '
            voting_graph += '"ul' + str(l) + '" '

        voting_graph += " [color=white] \n "

        for l in proposal_levels_keys:
            voting_graph += '{rank=same; "pl' + str(l) + '" '
            for p in proposal_levels[l]:
                if (p in bundled_proposals):
                    continue
                voting_graph += " " + str(p.id) + " "
            voting_graph += "}\n"

        for l in user_levels_keys:
            voting_graph += '{rank=same; "ul' + str(l) + '" '
            for u in user_levels[l]:
                if (u in bundled_users):
                    continue
                voting_graph += '"' + u.username + '" '
            voting_graph += "}\n"

        for kc2u in combined_users:
            details_table = '  '
            color = "black"
            fillcolor = "lightpink3"
            peripheries = 0

            if (highlight_proposal1 and
                    kc2u in proposal_endorsers[highlight_proposal1]):
                color = "red"
                peripheries = 1

            # Bundles which have highlighted user inside do not
            # have a line around
            if (highlight_user1 == kc2u):
                color = "black"
                peripheries = 0

            details_table = ' BGCOLOR="lightpink3" '
            details = ' fillcolor=white style=filled color=' +\
                color + ' peripheries=' + str(peripheries) + ' '

            voting_graph += self.write_bundled_users(
                kc2u.username,
                combined_users[kc2u],
                self.room, details,
                details_table)

        for e in endorsers:
            if (e in bundled_users or e in combined_users):
                continue

            color = "lightpink3"
            fillcolor = "lightpink3"
            peripheries = 0

            if (highlight_proposal1 and
                    e in proposal_endorsers[highlight_proposal1]):
                color = "red"
                peripheries = 1

            if (highlight_user1 == e):
                color = "red"
                peripheries = 1

            # Add id to user node
            voting_graph += '"' + e.username + '" [id=u' + str(e.id) +\
                ' shape=egg fillcolor=' +\
                fillcolor +\
                ' style=filled color=' + color + ' peripheries=' +\
                str(peripheries) + ' style=filled  fontsize=11]'
            voting_graph += "\n"

        keys = combined_proposals.keys()
        for kc2p in keys:

            details_table = '  '

            if (kc2p in pareto):
                color = "black"
                peripheries = 0
                endo = proposal_endorsers[kc2p]

                if (highlight_user1 and highlight_user1 in endo):
                    color = "red"
                    peripheries = 1

                if (highlight_proposal1):
                    if (kc2p in proposals_below[highlight_proposal1] or
                            kc2p in proposals_above[highlight_proposal1]):
                        color = "red"
                        peripheries = 1

                if (len(endo) == len(endorsers)):
                    details_table = ' BGCOLOR="gold" '
                else:
                    details_table = ' BGCOLOR="lightblue" '

                details = ' fillcolor=white style=filled color=' + color +\
                    ' peripheries=' + str(peripheries) + ' '
            else:
                color = "black"
                peripheries = 0

                if (highlight_user1 and
                        highlight_user1 in proposal_endorsers[kc2p]):
                    color = "red"
                    peripheries = 1

                if (highlight_proposal1):
                    if (kc2p in proposals_below[highlight_proposal1] or
                            kc2p in proposals_above[highlight_proposal1]):
                        color = "red"
                        peripheries = 1

                details = ' fillcolor=white color=' + color +\
                    ' peripheries=' + str(peripheries) + ' '

            voting_graph += self.write_bundled_proposals(
                kc2p.id, combined_proposals[kc2p], self.room,
                details,
                details_table,
                internal_links,
                highlight_proposal1)

        all_combined_proposals = set()
        for s in combined_proposals.values():
            all_combined_proposals.update(s)

        for p in proposals:

            app.logger.debug("Skip prop if in a bundle...")

            app.logger.debug("continue if %s in %s or in %s\n",
                             p,
                             bundled_proposals,
                             all_combined_proposals)

            if (p in bundled_proposals):
                app.logger.debug(
                    "Prop %s is in bundled_proposals - skip...", p)
                continue

            if (p in all_combined_proposals):
                app.logger.debug(
                    "Prop %s is in all_combined_proposals - skip...", p)
                continue

            color = "black"
            peripheries = 1

            if (highlight_user1 and highlight_user1 in proposal_endorsers[p]):
                color = "red"
                peripheries = 2

            if (highlight_proposal1):
                if (highlight_proposal1 == p):
                    color = "red"
                    peripheries = 3

                if (p in proposals_below[highlight_proposal1]
                        or p in proposals_above[highlight_proposal1]):
                    color = "red"
                    peripheries = 2

            if (p in pareto):
                endo = p.endorsers()

                if (len(endo) == len(endorsers)):
                    fillcolor = '"gold"'
                else:
                    fillcolor = '"lightblue" '

                if (not internal_links):
                    urlquery = self.create_proposal_url(p, self.room)
                    tooltip = self.create_proposal_tooltip(p)
                    voting_graph += str(p.id) +\
                        ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                        ' shape=box fillcolor=' + fillcolor +\
                        ' style=filled color=' + color + ' peripheries=' +\
                        str(peripheries) + ' tooltip="' + tooltip +\
                        '"  fontsize=11 URL="' + app.config['SITE_DOMAIN'] +\
                        '/viewproposal.py/' + urlquery + '" target="_top"]'
                else:
                    urlquery = self.create_internal_proposal_url(p)
                    voting_graph += str(p.id) +\
                        ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                        ' shape=box fillcolor=' + fillcolor +\
                        ' style=filled color=' + color + ' peripheries=' +\
                        str(peripheries) + ' tooltip="' +\
                        self.create_proposal_tooltip(p) +\
                        '"  fontsize=11 URL="' +\
                        internal_links + urlquery + '" target="_top"]'
                voting_graph += "\n"

            else:
                if (not internal_links):
                    urlquery = self.create_proposal_url(p, self.room)
                    internal_proposal_url =\
                        self.create_internal_proposal_url(p)
                    voting_graph += str(p.id) +\
                        ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                        ' shape=box color=' + color + ' peripheries=' +\
                        str(peripheries) + ' tooltip="' +\
                        internal_proposal_url +\
                        '"  fontsize=11 URL="' + app.config['SITE_DOMAIN'] +\
                        '/viewproposal.py/' + urlquery +\
                        '" target="_top"]'
                else:
                    urlquery = self.create_internal_proposal_url(p)
                    voting_graph += str(p.id) +\
                        ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                        ' shape=box color=' +\
                        color + ' peripheries=' + str(peripheries) +\
                        ' tooltip="' +\
                        self.create_proposal_tooltip(p) +\
                        '"  fontsize=11 URL="' +\
                        internal_links + urlquery + '" target="_top"]'
                voting_graph += "\n"

        for p in proposals:
            pcolor = "black"
            if (p in bundled_proposals):
                continue

            if (highlight_proposal1 and
                    (highlight_proposal1 == p or
                     p in proposals_below[highlight_proposal1])):
                pcolor = "red"

            pcs = proposals_covered[p]
            for pc in pcs:
                color = pcolor
                if (pc in bundled_proposals):
                    continue

                if (highlight_user1 in proposal_endorsers[pc]):
                    color = "red"

                # An empty array is trivially dominated by everything.
                #
                # But that is so trivial that it simplifies the graph
                # if we just do not show those lines.
                if (len(proposal_endorsers[pc]) == 0):
                    color = "white"

                if (highlight_proposal1 and
                        (highlight_proposal1 == pc or
                         pc in proposals_above[highlight_proposal1])):
                    color = "red"

                '''
                left_prop_id = ''
                if (pc in combined_proposals):
                    for prop in combined_proposals[pc]:
                        if (left_prop_id):
                            left_prop_id += '_'
                        left_prop_id += 'p' + str(prop.id)
                else:
                    left_prop_id += 'p' + str(pc.id)

                right_prop_id = ''
                if (p in combined_proposals):
                    for prop in combined_proposals[p]:
                        if (right_prop_id):
                            right_prop_id += '_'
                        right_prop_id += 'p' + str(prop.id)
                else:
                    right_prop_id += 'p' + str(p.id)
                '''

                left_prop_id = self.calculate_propsal_node_id(
                    pc,
                    combined_proposals)
                right_prop_id = self.calculate_propsal_node_id(
                    p,
                    combined_proposals)

                edge_id = 'id="' + left_prop_id + '&#45;' + '&#45;' +\
                    right_prop_id + '"'

                voting_graph += ' ' + str(pc.id) + ' -> ' + str(p.id) +\
                    ' [' + edge_id + ' class="edge" color="' + color + '"]'
                voting_graph += " \n"

        for e in endorsers:
            ecolor = "blue"
            if (e in bundled_users):
                continue

            ecs = endorsers_covered[e]

            if (highlight_user1 and
                    (highlight_user1 == e or
                     highlight_user1 in endorsers_above[e])):
                ecolor = "red"

            for ec in ecs:
                color = ecolor
                if (ec in bundled_users):
                    continue

                if (highlight_proposal1 in endorser_proposals[ec]):
                    color = "red"

                edge_id = 'id="u' + str(e.id) + '&#45;' + '&#45;' +\
                    'u' + str(ec.id) + '"'

                voting_graph += '"' + e.username + '" -> "' + ec.username +\
                    '"' +\
                    ' [' + edge_id + ' class="edge" color="' + color + '"]'
                voting_graph += " \n"

        new_proposals = dict()
        for e in endorsers:
            new_proposals[e] = self.new_proposals_to_an_endorser(
                endorser_proposals,
                e,
                endorsers_covered)

        for p in proposals:

            if (p in bundled_proposals):
                continue

            endorsers_to_this = self.new_endorsers_to_a_proposal(
                proposal_endorsers,
                p,
                proposals_covered)

            app.logger.debug("Proposal p ==> %s\n", p)

            app.logger.debug("endorsers_to_this ==> %s\n", endorsers_to_this)

            app.logger.debug("new_proposals ==> %s\n", new_proposals)

            for e in endorsers_to_this:

                app.logger.debug("Endorser e ==> %s\n", e)

                if (e in bundled_users):
                    app.logger.debug("e in bundled_users: continue...\n")
                    continue

                if (p.id not in new_proposals[e]):
                    app.logger.debug("%s not in %s: continue...\n",
                                     p, new_proposals[e])
                    continue

                color = "blue"

                if (highlight_user1 and
                        (highlight_user1 == e or
                         highlight_user1 in endorsers_above[e])):
                    color = "red"

                keys = combined_users.keys()
                if (e in keys):
                    if (highlight_user1 in combined_users[e]):
                        color = "red"

                if (highlight_proposal1 and
                        (highlight_proposal1 == p or
                         p in proposals_below[highlight_proposal1])):
                    color = "red"

                propnode_id = self.calculate_propsal_node_id(
                    p,
                    combined_proposals)
                edge_id = 'id="u' + str(e.id) + '&#45;' + '&#45;' +\
                    propnode_id + '"'

                voting_graph += ' "' + e.username + '" -> ' + str(p.id) +\
                    ' [' + edge_id + ' class="edge" color="' + color + '"]'
                voting_graph += " \n"

        voting_graph += "\n}"
        return voting_graph

    def calculate_propsal_node_id(self, proposal, combined_proposals):
        '''
        .. function:: calculate_propsal_node_id(proposal, combined_proposals)

        Calculates the node ID for a proposal or proposal group node.

        :param proposal: the proposal or index of a proposal group
        :type proposal: Proposal
        :param combined_proposals: proposals grouped into single nodes
        :type combined_proposals: dict
        :rtype: string
        '''
        prop_id = ''
        if (proposal in combined_proposals):
            for prop in combined_proposals[proposal]:
                if (prop_id):
                    prop_id += '_'
                prop_id += 'p' + str(prop.id)
        else:
            prop_id += 'p' + str(proposal.id)

        return prop_id

    def calculate_user_node_id(self, user, combined_users):
        '''
        .. function:: calculate_user_node_id(user, combined_users)

        Calculates the node ID for a user or user group node.

        :param user: the user or index of a user group
        :type user: User
        :param combined_users: users grouped into single nodes
        :type combined_users: dict
        :rtype: string
        '''
        user_id = ''
        if (user in combined_users):
            for usr in combined_users[user]:
                if (user_id):
                    user_id += '_'
                user_id += 'u' + str(usr.id)
        else:
            user_id += 'u' + str(user.id)

        return user_id

    def new_proposals_to_an_endorser(self,
                                     endorser_proposals,
                                     endorser,
                                     endorsers_covered):
        '''
        .. function:: new_proposals_to_an_endorser(endorser_proposals,
                                                   endorser,
                                                   endorsers_covered)

        Delete this proposal. Only available to the author during the
        question WRITING PHASE of the generation the proposal was first
        propsosed (created).

        :param user: user
        :type user: User
        :rtype: boolean
        '''
        below = endorsers_covered[endorser]
        voters_known = set()

        for b in below:
            voters_known.update(endorser_proposals[b])

        new_proposals = endorser_proposals[endorser] - voters_known

        app.logger.debug("new_proposals_to_an_endorser....\n")
        app.logger.debug("endorser INSIDE ==> %s\n", endorser)
        app.logger.debug("endorser_proposals INSIDE ==> %s\n",
                         endorser_proposals)
        app.logger.debug("endorsers_covered INSIDE ==> %s\n",
                         endorsers_covered)
        app.logger.debug("new_proposals INSIDE ==> %s\n", new_proposals)

        return new_proposals

    def new_endorsers_to_a_proposal(self,
                                    proposal_endorsers,
                                    proposal,
                                    proposals_covered):

        '''
        app.logger.debug("new_endorsers_to_a_proposal....\n")
        app.logger.debug("proposal INSIDE ==> %s\n", proposal)
        app.logger.debug("proposal_endorsers INSIDE ==> %s\n",
                         proposal_endorsers)
        app.logger.debug("proposals_covered INSIDE ==> %s\n",
                         proposals_covered)
        '''

        below = proposals_covered[proposal]
        # app.logger.debug("below INSIDE ==> %s\n", below)

        voters_known = set()
        for b in below:
            '''
            app.logger.debug("proposal_endorsers[b] INSIDE ==> %s\n",
                proposal_endorsers[b])
            '''
            voters_known.update(proposal_endorsers[b])

        # app.logger.debug("voters_known INSIDE ==> %s\n", voters_known)

        new_endorsers = proposal_endorsers[proposal] - voters_known

        # app.logger.debug("new_endorsers INSIDE ==> %s\n", new_endorsers)

        return new_endorsers

    def write_bundled_proposals(self, bundle_name, bundle_content,
                                room, details, details_table,
                                internal_links, highlight_proposal1=None):

        app.logger.debug("write_bundled_proposals.....\n")
        app.logger.debug("bundle_name => %s\n", bundle_name)
        app.logger.debug("bundle_content => %s\n", bundle_content)
        app.logger.debug("details_table => %s\n", details_table)
        app.logger.debug("details => %s\n", details)

        bundle_size = len(bundle_content)

        node_id = ''
        for p in bundle_content:
            if (node_id):
                node_id += '_'
            node_id += 'p' + str(p.id)

        bundle = str(bundle_name) + ' [id=' + node_id + ' shape=plaintext ' +\
            details +\
            ' fontsize=11 label=<<TABLE BORDER="0" ' +\
            details_table + ' CELLBORDER="1" CELLSPACING="0" ' +\
            'CELLPADDING="4"><TR><TD COLSPAN="' +\
            str(bundle_size) + '"></TD></TR><TR>'

        for p in bundle_content:
            urlquery = self.create_proposal_url(p, room)
            # This is weird, in all the rest of the map an & is an &
            # but here he wants them as a &amp
            urlquery.replace('&', '&amp')

            tooltip = self.create_proposal_tooltip(p)
            # This is weird, in all the rest of the map an & is an &
            # but here he wants them as a &amp
            tooltip.replace('&', '&amp')
            to_add = ''
            if (highlight_proposal1 == p):
                to_add = ' BGCOLOR="red" '

            if (not internal_links):
                bundle += '<TD ' + to_add + ' HREF="HTTP://' +\
                    app.config['SITE_DOMAIN'] +\
                    '/viewproposal.py/' +\
                    urlquery + '" tooltip="' + tooltip + '" target="_top">' +\
                    str(p.id) + '</TD>'
            else:
                urlquery = self.create_internal_proposal_url(p)
                # This is weird, in all the rest of the map an & is an &
                # but here he wants them as a &amp
                internal_links.replace('&', '&amp')
                bundle += '<TD ' + to_add + ' HREF="HTTP://' +\
                    internal_links + urlquery +\
                    '" tooltip="' + tooltip + '" target="_top">' +\
                    str(p.id) + '</TD>'

        bundle += '</TR><TR><TD COLSPAN="' + str(bundle_size) +\
            '"></TD></TR></TABLE>>]'
        bundle += "\n"
        return bundle

    def write_bundled_users(self, bundle_name, bundle_content, room,
                            details, details_table, highlight_user1=None):

        node_id = ''
        for user in bundle_content:
            if (node_id):
                node_id += '_'
            node_id += 'p' + str(user.id)

        # ' [shape=plaintext ' +\
        bundle = '"' + bundle_name + '" ' +\
            ' [id=' + node_id + ' shape=plaintext ' +\
            details + ' fontsize=11 label=<<TABLE BORDER="0" ' +\
            details_table +\
            ' CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">'

        if (highlight_user1 and highlight_user1 in bundle_content):
            u = highlight_user1
            urlquery = str(u.id)
            tooltip = u.username
            # In all the rest of the map an & is an &
            # but here he wants them as a &amp
            # tooltip = str_replace ( "&" , "&amp" , tooltip )
            to_add = ''
            # We write the highlighted user before and on a different color
            to_add = ' BGCOLOR="red" '
            bundle += '<TR><TD ' + to_add + ' HREF="' +\
                app.config['SITE_DOMAIN'] +\
                '/user+php?u=' +\
                urlquery + '" tooltip="' + tooltip + '" target="_top">' +\
                u.username + '</TD></TR>'

        for u in bundle_content:
            # This has already been written
            if (highlight_user1 and highlight_user1 == u):
                continue

            urlquery = ' HREF="' + str(u.id)
            tooltip = u.username
            bundle += '<TR><TD ' + ' HREF="' + app.config['SITE_DOMAIN'] +\
                '/user/u=' + urlquery +\
                '" tooltip="' + tooltip + '" target="_top">' +\
                u.username + '</TD></TR>'

        bundle += '</TABLE>>]'
        bundle += "\n"
        return bundle

    def strip_tags(self, html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()

    def string_safe(self, s):
        import string
        s = self.strip_tags(s)
        s = string.replace(s, '"', "'")
        s = string.replace(s, '\n', " ")
        s = string.replace(s, '&nbsp;', " ")
        s = string.replace(s, '\r', " ")
        s = string.replace(s, '\r\n', " ")
        return s

    def create_proposal_tooltip(self, proposal):
        if (len(proposal.abstract) > 0):
            tooltip = self.string_safe(proposal.abstract)
        else:
            tooltip = self.string_safe(proposal.blurb)
        return tooltip[:800]

    def create_internal_proposal_url(self, proposal):
        return "#proposal" + str(proposal.id)

    def create_proposal_url(self, proposal, room):
        return str(proposal.id) + '/' + room

    def get_covered(self, elements_below, elements):
        '''
        .. function:: get_covered(elements_below, elements)

        Returns all elements with a list of
        elements below them on the graph.

        :param elements_below: what elements lie below each element.
        :type elements_below: dict
        :param elements: set of all elements on the graph.
        :type elements: set
        :rtype: dict
        '''
        covered = dict()
        for element in elements:
            covered_elements = set()
            below = elements_below[element]
            for element1 in below:
                for element2 in below:
                    next_element = False
                    under_element2 = elements_below[element2]
                    if (element1 in under_element2):
                        next_element = True
                        break
                if (next_element):
                    continue
                covered_elements.add(element1)
            covered[element] = covered_elements
        return covered

    def find_levels(self, elements_covered, elements):
        '''
        .. function:: find_levels(elements_covered, elements)

        Sorts the elements into lavels based on which elements cover
        other elements.

        :param elements_covered: what elements lie below each element.
        :type elements_covered: dict
        :param elements: set of all elements on the graph.
        :type elements: set
        :rtype: dict
        '''
        # app.logger.debug("find_levels called...\n")

        elements_to_test = copy.copy(elements)
        # app.logger.debug("elements_to_test = %s\n", elements_to_test)
        levels = dict()
        level = 0
        elements_added = set()
        while (len(elements_added) < len(elements)):
            levels[level] = set()
            for element1 in elements_to_test:
                next_element = False
                for element2 in elements_to_test:
                    if (element1 in elements_covered[element2]):
                        next_element = True
                        break
                if (next_element):
                    continue
                levels[level].add(element1)
                elements_added.add(element1)
            elements_to_test = elements - elements_added
            # app.logger.debug("elements_to_test = %s\n", elements_to_test)
            level += 1
        return levels

    def find_levels_based_on_size(self, A_to_B):
        '''
        .. function:: find_levels_based_on_size(A_to_B)

        Returns a list of IDs of element type A sorted into levels based
        on the number of elements of type B they are related to.

        Used to sort proposal and user nodes into levels.

        :param A_to_B: Elements of type B related to each element of type A.
        :type A_to_B: dict
        :rtype: dict
        '''
        app.logger.debug("find_levels_based_on_size called with %s\n",
                         A_to_B)
        level_from_length = dict()
        for (element_A, related) in A_to_B.iteritems():
            level = len(related)
            if (level not in level_from_length):
                level_from_length[level] = set()
            level_from_length[level].add(element_A)

        levels = dict()
        keys = sorted(level_from_length.keys())
        for key in keys:
            levels[key] = level_from_length[key]
        return levels

    def combine_proposals(self, proposal_endorsers, proposals=None):
        '''
        .. function:: combine_proposals(proposal_endorsers[, proposals=None])

        Returns a dictionary of all elements with a list of
        elements above them on the graph.

        :param proposal_endorsers: what elements lie below each element.
        :type proposal_endorsers: dict
        :param proposals: set of all elements
        :type proposals: set
        :rtype: dict
        '''

        app.logger.debug("combine_proposals called....\n")
        app.logger.debug("proposal_endorsers %s\n",
                         proposal_endorsers)
        app.logger.debug("proposals %s\n",
                         proposals)

        if (proposals == 0):
            proposals = proposal_endorsers.keys()
        else:
            proposals = list(proposals)

        proposals = sorted(proposals, key=lambda prop: prop.id)
        app.logger.debug("proposals as sorted list %s\n",
                         proposals)

        combined_to_proposals = dict()
        proposals_to_combined = dict()

        for proposal in proposals:
            proposals_to_combined[proposal] = proposal

        app.logger.debug("proposals_to_combined %s\n",
                         proposals_to_combined)

        for proposal1 in proposals:
            if (proposals_to_combined[proposal1] != proposal1):
                continue

            for proposal2 in proposals:
                if (proposal1.id >= proposal2.id or
                        proposals_to_combined[proposal2] != proposal2):
                    continue

                endorsers1 = proposal_endorsers[proposal1]
                endorsers2 = proposal_endorsers[proposal2]

                app.logger.debug("Comparing Endorsers\n")
                app.logger.debug("endorsers1 %s\n",
                                 endorsers1)
                app.logger.debug("endorsers2 %s\n",
                                 endorsers2)

                compare_endorsers = (
                    endorsers1 | endorsers2) - (endorsers1 & endorsers2)
                app.logger.debug("compare_endorsers %s\n",
                                 compare_endorsers)

                app.logger.debug("proposals_to_combined %s\n",
                                 proposals_to_combined)

                '''
                if (endorsers1 == endorsers2):
                    proposals_to_combined[proposal2] =\
                        proposals_to_combined[proposal1]
                    combined_to_proposals[proposals_to_combined[proposal1]] =\
                        list()
                '''
                if (len((endorsers1 | endorsers2) -
                        (endorsers1 & endorsers2)) == 0):
                    proposals_to_combined[proposal2] =\
                        proposals_to_combined[proposal1]
                    combined_to_proposals[proposals_to_combined[proposal1]] =\
                        set()

        for proposal1 in proposals:
            if (proposals_to_combined[proposal1] != proposal1):
                combined_to_proposals[proposals_to_combined[proposal1]].\
                    add(proposal1)

        return combined_to_proposals

    def combine_users(self, proposal_endorsers, endorsers, generation):
        '''
        .. function:: combine_users(elements_covered, elements)

        Returns a dictionary of all elements with a list of
        elements above them on the graph.

        :param elements_covered: what elements lie below each element.
        :type elements_covered: dict
        :param elements: set of all elements on the graph.
        :type elements: set
        :rtype: dict
        '''
        app.logger.debug("combine_users called...\n")

        endorsers = list(endorsers)
        endorsers = sorted(endorsers, key=lambda end: end.id)
        app.logger.debug("endorsers as sorted list %s\n",
                         endorsers)

        combined_to_endorsers = dict()
        endorsers_to_combined = dict()

        for endorser in endorsers:
            endorsers_to_combined[endorser] = endorser

        for endorser1 in endorsers:
            if (endorsers_to_combined[endorser1] != endorser1):
                continue

            for endorser2 in endorsers:
                if (endorser1.id >= endorser2.id or
                        endorsers_to_combined[endorser2] != endorser2):
                    continue

                app.logger.debug("Comparing Endorsments for users %s and %s\n",
                                 endorser1.username, endorser2.username)
                app.logger.debug(
                    "endorser1 endorsed %s\n",
                    endorser1.get_endorsed_proposal_ids(self, generation))
                app.logger.debug(
                    "endorser2 endorsed %s\n",
                    endorser2.get_endorsed_proposal_ids(self, generation))

                if (endorser1.get_endorsed_proposal_ids(self, generation) ==
                        endorser2.get_endorsed_proposal_ids(self, generation)):
                    '''
                    If U is already part of a bundle it will point to its
                    lowest member, if not we point endorser2 to endorser1
                    (which is lower)
                    '''
                    endorsers_to_combined[endorser2] =\
                        endorsers_to_combined[endorser1]
                    combined_to_endorsers[endorsers_to_combined[endorser1]] =\
                        list()

        for endorser1 in endorsers:
            if(endorsers_to_combined[endorser1] != endorser1):
                combined_to_endorsers[endorsers_to_combined[endorser1]].\
                    append(endorser1)

        return combined_to_endorsers

    def __repr__(self):
        return "<Question('%s',auth: '%s', '%s')>" % (self.title,
                                                      self.author.username,
                                                      self.phase)


class Generation():
    _question = None
    _generation = None
    _pareto_front = None
    _key_players = None
    _endorsers = None
    _endorser_effects = None
    _proposals = None

    @property
    def question(self):
        return self._question

    @property
    def generation(self):
        return self._generation

    @property
    def proposals(self):
        '''
        Proposals

        The list of the proposals for this generation.

        :rtype: list
        '''
        if (self._proposals is not None):
            return self._proposals
        else:
            result = self.question.history.filter(and_(
                QuestionHistory.question_id == self.question.id,
                QuestionHistory.generation == self.generation
            )).all()
            self._proposals = set()
            for entry in result:
                self._proposals.add(entry.proposal)
            return self._proposals

    @property
    def proposal_ids(self):
        '''
        Proposals

        The list of the proposals for this generation.

        :rtype: list
        '''
        proposals = self.proposals
        proposal_ids = set()
        for proposal in proposals:
            proposal_ids.add(proposal.id)
        return proposal_ids

    def calculate_pareto_front(self):
        self._pareto_front = self.question.calculate_pareto_front(
            proposals=self.proposals,
            generation=self.generation,
            save=True)
        return self._pareto_front

    def calculate_pareto_front_ids(self):
        self.calculate_pareto_front()
        return self.pareto_front_ids

    @property
    def pareto_front(self):
        '''
        Pareto front

        The pareto front for this generation.

        :rtype: set
        '''
        if (self._pareto_front is not None):
            return self._pareto_front
        else:
            pareto_history = self.question.history.filter(and_(
                QuestionHistory.question_id == self.question.id,
                QuestionHistory.generation == self.generation,
                QuestionHistory.dominated_by == 0
            )).all()
            self._pareto_front = set()
            for entry in pareto_history:
                self._pareto_front.add(entry.proposal)
            return self._pareto_front

    @property
    def pareto_front_ids(self):
        pareto_front = self.pareto_front
        pareto_front_ids = set()
        for proposal in pareto_front:
            pareto_front_ids.add(proposal.id)
        return pareto_front_ids

    @property
    def endorsers(self):
        '''
        Endorsers

        The list of endorsers for this generation.

        :rtype: list of Users
        '''
        proposals = self.proposals
        self._endorsers = set()
        for proposal in proposals:
            self._endorsers.update(proposal.endorsers(self.generation))
        return self._endorsers

    @property
    def key_players(self):
        '''
        key_players

        The list of endorsers identified as being key players for
        this generation.

        :rtype: list of Users
        '''
        if (self._key_players is not None):
            return self._key_players
        else:
            key_player_history = self.question.key_players.\
                order_by(KeyPlayer.user_id).filter(and_(
                    KeyPlayer.question_id == self.question.id,
                    KeyPlayer.generation == self.generation,
                )).all()
            self._key_players = dict()
            for entry in key_player_history:
                if (entry.user_id not in self._key_players):
                    self._key_players[entry.user_id] = set()
                self._key_players[entry.user_id].add(entry.proposal)
            return self._key_players

    def calculate_proposal_relations(self):
        '''
        .. function:: calculate_proposal_relations()

        Calculates the complete map of dominations. For each proposal
        it calculates which proposals dominate and which are dominated.

        :rtype: dict
        '''
        proposal_relations = dict()
        props = dict()
        all_proposals = self.proposals
        for p in all_proposals:
            props[p.id] = p.set_of_endorser_ids(self.generation)

        for proposal1 in all_proposals:
            dominating = set()
            dominated = set()
            proposal_relations[proposal1] = dict()

            for proposal2 in all_proposals:
                if (proposal1 == proposal2):
                    continue
                who_dominates = Proposal.\
                    who_dominates_who(props[proposal1.id],
                                      props[proposal2.id])
                '''
                app.logger.debug("Comparing props %s %s and %s %s\n",
                                 proposal1.id, props[proposal1.id],
                                 proposal2.id, props[proposal2.id])
                app.logger.debug("   ===> WDW Result = %s\n",
                                 who_dominates)
                '''
                if (who_dominates == props[proposal1.id]):
                    dominating.add(proposal2)
                elif (who_dominates == props[proposal2.id]):
                    dominated.add(proposal2)

            proposal_relations[proposal1]['dominating'] = dominating
            proposal_relations[proposal1]['dominated'] = dominated

        return proposal_relations

    def calculate_key_players(self):
        '''
        .. function:: calculate_key_players()

        Calculates the effects each endorser has on the pareto.
        What would be the effects if he didn't vote?
        What proposals has he forced into the pareto?

        :rtype: dict
        '''
        key_players = dict()

        app.logger.debug("+++++++++++ calculate_key_players() +++++++++++")

        all_endorsers = self.endorsers
        pareto = self.pareto_front
        if (len(pareto) == 0):
            return dict()

        for user in all_endorsers:
            app.logger.debug("+++++++++++ Checking User +++++++++++ %s\n",
                             user.id)

            users_endorsed_proposal_ids =\
                user.get_endorsed_proposal_ids(self.question, self.generation)

            app.logger.debug(">>>>>>>>>> Users endorsed proposal IDs %s\n",
                             users_endorsed_proposal_ids)
            app.logger.debug("Calc PF excluding %s\n", user.id)

            new_pareto = self.question.calculate_pareto_front(
                proposals=pareto,
                generation=self.generation,
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
                                                              user,
                                                              self.generation))
                    app.logger.debug(
                        "Pareto Props that could dominate PID %s %s\n",
                        users_proposal.id,
                        key_players[user.id])
            else:
                app.logger.debug("%s is not a key player\n", user.id)

        #self.question.save_key_players(key_players)
        app.logger.debug("Generation.calc_key_players: %s", key_players)
        return key_players

    @property
    def endorser_effects(self):
        '''
        .. function:: endorser_effects()

        Calculates the effects each endorser has on the pareto.
        What would be the effects if he didn't vote?
        What proposals has he forced into the pareto?

        To do: Will propbably store these calculations in a table

        :rtype: dict
        '''
        if (self._endorser_effects is not None):
            return self._endorser_effects
        else:
            all_endorsers = self.endorsers
            app.logger.debug("All Endorsers: %s\n", all_endorsers)
            pareto = self.pareto_front
            self._endorser_effects = dict()
            for endorser in all_endorsers:
                PF_excluding_endorser = self.question.calculate_pareto_front(
                    proposals=self.proposals,
                    generation=self.generation,
                    exclude_user=endorser)
                PF_plus = PF_excluding_endorser - pareto
                PF_minus = pareto - PF_excluding_endorser
                if (len(PF_plus) or len(PF_minus)):
                    self._endorser_effects[endorser] = {
                        'PF_excluding': PF_excluding_endorser,
                        'PF_plus': PF_plus,
                        'PF_minus': PF_minus}
                else:
                    self._endorser_effects[endorser] = None
            return self._endorser_effects

    def __init__(self, question, generation):
        self._question = question
        self._generation = generation or question.generation

    def __repr__(self):
        return "<Generation(G'%s', Q'%s')>" % (self.generation,
                                               self.question.id)

    def __str__(self):
        return "Generation %s for Question %s" % (self.generation,
                                                  self.question.id)


class KeyPlayer(Base):
    '''
    Stores key player information for each geenration
    '''
    __tablename__ = "key_player"

    user_id = Column(Integer, ForeignKey('user.id'),
                     primary_key=True, autoincrement=False)
    proposal_id = Column(Integer, ForeignKey('proposal.id'),
                         primary_key=True, autoincrement=False)
    question_id = Column(Integer, ForeignKey('question.id'),
                         primary_key=True, autoincrement=False)
    generation = Column(Integer, primary_key=True, autoincrement=False)

    proposal = relationship("Proposal", cascade="all, delete-orphan",
                            single_parent=True)
    user = relationship("User", cascade="all, delete-orphan",
                        single_parent=True)

    def __init__(self, user_id, proposal_id, question_id, generation):
        self.user_id = user_id
        self.proposal_id = proposal_id
        self.question_id = question_id
        self.generation = generation

    def __repr__(self):
        return "<KeyPlayer('%s','%s','%s', '%s')>" % (self.user_id,
                                                      self.proposal_id,
                                                      self.generation,
                                                      self.question_id)


class VotingComments(Base):
    '''
    Holds comments made during voting when disagreeing with a proposal or
    not understanding one enough.
    '''

    __tablename__ = 'voting_comments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    proposal_id = Column(Integer)
    created = Column(DateTime)
    comment = Column(Text, nullable=False)
    comment_type = Column(Enum('confused', 'disagree'), nullable=False)

    def __init__(self, user, proposal, comment, comment_type):
        self.user_id = user.id
        self.proposal_id = proposal.id
        self.created = datetime.datetime.utcnow()
        self.comment = comment
        self.comment_type = comment_type


class QuestionHistory(Base):
    '''
    Represents the QuestionHistory object which holds the historical
    proposal data for the question.

    Proposal data is copied here when the question is moved on to
    the writing stage.
    '''

    __tablename__ = 'question_history'

    proposal_id = Column(Integer, ForeignKey('proposal.id'),
                         primary_key=True, autoincrement=False)
    question_id = Column(Integer, ForeignKey('question.id'),
                         primary_key=True, autoincrement=False)
    generation = Column(Integer, primary_key=True, autoincrement=False)
    dominated_by = Column(Integer, nullable=False, default=0)

    def __init__(self, proposal):
        self.proposal_id = proposal.id
        self.question_id = proposal.question_id
        self.generation = proposal.question.generation
        #self.generation_created = proposal.generation_created
        #self.dominated_by = proposal.dominated_by

    def __repr__(self):
        return "<Generation('%s','%s','%s', '%s')>" % (self.question_id,
                                                       self.generation,
                                                       self.proposal_id,
                                                       self.dominated_by)


class Proposal(Base):
    '''
    Represents the proposal object
    '''

    __tablename__ = 'proposal'

    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    blurb = Column(Text, nullable=False)
    abstract = Column(Text)
    #generation = Column(Integer, default=1)
    generation_created = Column(Integer, default=1)
    created = Column(DateTime)
    user_id = Column(Integer, ForeignKey('user.id'))
    question_id = Column(Integer, ForeignKey('question.id'))
    #dominated_by = Column(Integer, default=0)
    # 1:M
    endorsements = relationship('Endorsement', backref="proposal",
                                lazy='dynamic', cascade="all, delete-orphan")

    history = relationship('QuestionHistory',
                           backref=backref("proposal", lazy="joined"),
                           lazy='joined', cascade="all, delete-orphan")

    def __init__(self, author, question, title, blurb, abstract=None):
        self.user_id = author.id
        self.question_id = question.id
        self.title = title
        self.blurb = blurb
        #self.generation = question.generation
        self.generation_created = question.generation
        self.created = datetime.datetime.utcnow()
        self.abstract = abstract
        self.question = question

    def publish(self):
        self.history.append(QuestionHistory(self))

    def update(self, user, title, blurb):
        '''
        .. function:: update(user, title, blurb)

        Update the title and content of this proposal. Only available to the
        author during the question WRITING PHASE of the generation the
        proposal was first propsosed (created).

        :param user: user
        :type user: User object
        :param title: updated proposal title
        :type title: string
        :param blurb: updated proposal content
        :type blurb: string
        :rtype: boolean
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
        .. function:: delete(user)

        Delete this proposal. Only available to the author during the
        question WRITING PHASE of the generation the proposal was first
        propsosed (created).

        :param user: user
        :type user: User
        :rtype: boolean
        '''
        if (user == self.user_id
                and self.question.phase == 'writing'
                and self.question.generation == self.generation_created):
                    db_session.delete(self)
                    return True
        else:
            return False

    def endorse(self, endorser):
        '''
        .. function:: endorse(endorser)

        Add a user's endorsement to this proposal.

        :param endorser: user
        :type endorser: User object
        '''
        self.endorsements.append(Endorsement(endorser, self))
        return self

    def remove_endorsement(self, endorser):
        '''
        .. function:: remove_endorsement(endorser)

        Remove a user's endorsement from this proposal.

        :param endorser: user
        :type endorser: User object
        '''
        endorsement = self.endorsements.filter(and_(
            Endorsement.user_id == endorser.id,
            Endorsement.proposal_id == self.id,
            Endorsement.generation == self.question.generation)
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
        generation = generation or self.question.generation

        return self.endorsements.filter(and_(
            Endorsement.user_id == user.id,
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation)
        ).count() == 1

    def endorsers(self, generation=None):
        '''
        .. function:: endorsers([generation=None])

        Returns a set of the current endorsers
            - Defaults to current generation

        :param generation: question generation
        :type generation: integer or None
        :rtype: set
        '''
        generation = generation or self.question.generation
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
        generation = generation or self.question.generation
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
        :type proposal1: set of integers
        :param proposal2: set of voters for proposal 2
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
        return "<Proposal('%s', Q:'%s')>"\
            % (self.id,
               self.question_id)


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
        self.user_id = endorser.id
        self.proposal_id = proposal.id
        self.generation = proposal.question.generation
        self.endorsement_date = datetime.datetime.utcnow()


@event.listens_for(Proposal, "after_insert")
def after_insert(mapper, connection, target):
    connection.execute(
        QuestionHistory.__table__.insert().
        values(proposal_id=target.id, question_id=target.question.id,
               generation=target.question.generation)
    )


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)
