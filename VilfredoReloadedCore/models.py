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

from sqlalchemy import Enum, DateTime, Text

from sqlalchemy.orm import relationship

from .database import Base

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
    password = Column(String(60))
    registered = Column(DateTime)
    last_seen = Column(DateTime)
    # 1:M
    questions = relationship('Question', backref='author', lazy='dynamic')
    proposals = relationship('Proposal', backref='author', lazy='dynamic')
    endorsements = relationship('Endorsement',
                                backref='endorser', lazy='dynamic')
    # updates 1:M
    subscribed_questions = relationship("Update", backref='subscriber',
                                        lazy='dynamic')
    # invites M:M
    invites = relationship("Invite", primaryjoin="User.id==Invite.sender_id",
                           backref="sender", lazy='dynamic')

    def invite(self, receiver, question_id):
        self.invites.append(Invite(receiver, question_id))
        return self

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
    generation = Column(Integer, default=1)
    created = Column(DateTime)
    room = Column(String(20))
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
    title = Column(String(120))
    blurb = Column(Text, nullable=False)
    generation = Column(Integer, default=1)
    created = Column(DateTime)
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
        self.generation = 1
        self.created = datetime.datetime.utcnow()

    def endorse(self, endorser):
        self.endorsements.append(Endorsement(endorser, self))
        return self

    def remove_endorsement(self, endorser):
        pass

    @staticmethod
    def who_dominates_who(p1, p2):
        '''
        Takes 2 SETS of ENDORSER IDs, one for each proposal,
        and calulates which of any domiantes the other.

        Returns the dominating non-empty proposal set or ---
        -1 if both sets are the same
        0 if both sets are different
        '''

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
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    proposal_id = Column(Integer, ForeignKey('proposal.id'), nullable=False)
    endorsement_date = Column(DateTime)
    generation = Column(Integer, nullable=False)

    def __init__(self, endorser, proposal):
        self.endorser = endorser
        self.proposal = proposal
        self.generation = proposal.generation
        self.endorsement_date = datetime.datetime.utcnow()
