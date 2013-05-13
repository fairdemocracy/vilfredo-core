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


class User(Base):
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
        self.invites.append(Invite(receiver, question.id))
        return self

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

    def get_proposals(self, question, generation=None):
        generation = generation or question.generation
        return self.proposals.filter(and_(
            Proposal.question == question,
            Proposal.generation == generation)
        ).all()

    def delete_proposal(self, prop):
        proposal = self.proposals.filter(and_(
            Proposal.id == prop.id,
            Proposal.user_id == self.id
        )).first()
        if (proposal is not None
                and proposal.question.phase == 'writing'
                and
                proposal.question.generation == proposal.generation_created):
            self.proposals.remove(proposal)
        return self

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

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.registered = datetime.datetime.utcnow()
        self.last_seen = datetime.datetime.utcnow()

    def __repr__(self):
        return "<Vilfredo User('%s','%s', '%s')>" % (self.username,
                                                     self.email,
                                                     self.password)


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
    created = Column(DateTime)
    room = Column(String(20), default='')
    phase = Column(Enum('writing', 'voting', 'archived'), default='writing')
    last_move_on = Column(DateTime)
    user_id = Column(Integer, ForeignKey('user.id'))
    # 1:M
    proposals = relationship('Proposal', backref='question', lazy='dynamic')

    def __init__(self, author, title, blurb, room=None):
        self.author = author
        self.title = title
        self.blurb = blurb
        self.room = room or ''
        self.created = datetime.datetime.utcnow()

    def change_phase(self, phase=None):
        if (phase is None):
            if (self.phase == 'writing'):
                self.phase = 'voting'
            else:
                self.phase = 'writing'
        else:
            self.phase = phase
        return self

    def current_proposals_ids(self):
        if (self.proposals.count() == 0):
            return set()
        else:
            prop_ids = set()
            for p in self.proposals:
                prop_ids.add(p.id)
            return prop_ids

    def get_proposals(self, generation=None):
        generation = generation or self.generation
        return self.proposals.filter(
            Proposal.generation == generation
        ).all()

    def calculate_pareto_front(self, generation=None):
        '''
        Returns a SET containing the paret front proposal ids
        '''
        proposals = self.get_proposals(generation)

        if (len(proposals) == 0):
            return set()
        else:
            dominated = set()
            props = dict()

            for p in proposals:
                props[p.id] = p.set_of_endorser_ids()

            pids = props.keys()
            done = list()
            for p1 in pids:
                done.append(p1)
                for p2 in pids:
                    if (p2 in done):
                        continue

                    who_dominates = Proposal.\
                        who_dominates_who_2(props[p1], props[p2])
                    if (who_dominates == 0 or who_dominates == -1):
                        continue
                    elif (who_dominates == props[p1]):
                        dominated.add(p2)
                    elif (who_dominates == props[p2]):
                        dominated.add(p1)

            pareto = set()
            if (len(dominated) > 0):
                pareto = set(pids).difference(dominated)

            return pareto

    def __repr__(self):
        return "<User('%s','%s', '%s')>" % (self.title,
                                            self.blurb,
                                            self.author.username)


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
                                lazy='dynamic')

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
        Returns True if the user has endorsed in the current generation
            - Defaults to current generation
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

        current_endorsements = self.endorsements.filter(and_(
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation)
        ).all()
        endorsers = set()
        for e in current_endorsements:
            endorsers.add(e.endorser)
        return endorsers

    def set_of_endorser_ids(self, generation=None):
        endorsers = self.endorsers(generation)
        endorser_ids = set()
        for endorser in endorsers:
            endorser_ids.add(endorser.id)
        return endorser_ids

    @staticmethod
    def who_dominates_who_2(p1, p2):
        '''
        Takes 2 SETS of ENDORSER IDs, one for each proposal,
        and calulates which of any domiantes the other.

        Returns the dominating non-empty proposal set or ---
        -1 if both sets are the same
        0 if both sets are different
        '''
        # If p1 and p2 are the same return -1
        if (p1 == p2):
            return -1
        # If p1 is empty return p2
        elif (len(p1) == 0):
            return p2
        # If p2 is empty return p1
        elif (len(p2) == 0):
            return p1
        # Check if p1 is a propoer subset of p2
        elif (p1 < p2):
            return p2
        # Check if p2 is a proper subset of p1
        elif (p2 < p1):
            return p1
        # p1 and p2 are different return 0
        else:
            return 0

    @staticmethod
    def who_dominates_who(p1, p2):
        '''
        Takes 2 SETS of ENDORSER IDs, one for each proposal,
        and calulates which of any domiantes the other.

        Returns the dominating non-empty proposal set or ---
        -1 if both sets are the same
        0 if both sets are different
        '''
        # Check if the same
        if (p1 == p2):
            return -1
        # Check if p1 is empty
        if (len(p1) > 0):
            # Check if p2 is empty
            if (len(p2) > 0):
                # Check if p1 cpntains elements not in p2
                if (len(p1.difference(p2)) > 0):
                    # Check if p2 cpntains elements not in p1
                    if (len(p2.difference(p1)) > 0):
                        # Sets are different, neither dominates
                        return 0
                    else:
                        # p2 is a subset of p1 so p1 dominates
                        return p1
                else:
                    if (len(p2.difference(p1)) > 0):
                        # p1 is a subset of p2 so p2 dominates
                        return p2
                    else:
                        # Both are the same so neither dominates
                        return -1
            else:
                # p2 is empty and p2 is non-empty so p2 dominates
                return p1
        elif (len(p2) > 0):
            # p1 is empty and p2 is non-empty so p2 dominates
            return p2
        else:
            # Both are empty so neither dominates
            return -1

    def __repr__(self):
        return "<User('%s','%s', '%s', '%s')>" % (self.title,
                                                  self.blurb,
                                                  self.author.username,
                                                  self.question_id)


class Endorsement(Base):
    '''
    Stores endorsement data
    '''

    __tablename__ = 'endorsement'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    proposal_id = Column(Integer, ForeignKey('proposal.id'))
    endorsement_date = Column(DateTime)
    generation = Column(Integer, nullable=False)

    def __init__(self, endorser, proposal):
        self.endorser = endorser
        self.proposal = proposal
        self.generation = proposal.generation
        self.endorsement_date = datetime.datetime.utcnow()
