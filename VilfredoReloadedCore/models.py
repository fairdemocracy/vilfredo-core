#!/usr/bin/env python
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
The database Bases
'''

from sqlalchemy import and_, or_, not_, event, distinct, func

from database import db_session, db

import datetime, math, time

import copy, os, glob

from werkzeug.security import check_password_hash, generate_password_hash

from flask.ext.login import UserMixin

from . import app, emails

from HTMLParser import HTMLParser

from flask import url_for

import cPickle as pickle

##################################################
# Functions to calculate Geometric Median
##################################################
def candMedian(dataPoints):
    #Calculate the first candidate median as the geometric mean
    tempX = 0.0
    tempY = 0.0

    for i in range(0,len(dataPoints)):
        tempX += dataPoints[i][0]
        tempY += dataPoints[i][1]

    return [tempX/len(dataPoints),tempY/len(dataPoints)]

def median(mylist):
    sorts = sorted(mylist)
    length = len(sorts)
    if not length % 2:
        return (sorts[length / 2] + sorts[length / 2 - 1]) / 2.0
    return sorts[length / 2]

def numersum(testMedian,dataPoint):
    # Provides the numerator of the weiszfeld algorithm depending on whether you are adjusting the candidate x or y
    return 1/math.sqrt((testMedian[0]-dataPoint[0])**2 + (testMedian[1]-dataPoint[1])**2)

def denomsum(testMedian, dataPoints):
    # Provides the denominator of the weiszfeld algorithm
    print 'testMedian=' + str(testMedian)
    temp = 0.0
    for i in range(0,len(dataPoints)):
        if testMedian == dataPoints:
            continue
        temp += 1/math.sqrt((testMedian[0] - dataPoints[i][0])**2 + (testMedian[1] - dataPoints[i][1])**2)
    return temp

def objfunc(testMedian, dataPoints):
    # This function calculates the sum of linear distances from the current candidate median to all points
    # in the data set, as such it is the objective function we are minimising.
    temp = 0.0
    for i in range(0,len(dataPoints)):
        temp += math.sqrt((testMedian[0]-dataPoints[i][0])**2 + (testMedian[1]-dataPoints[i][1])**2)
    return temp

def findGeometricMedian(dataPoints):
    # Return if too few points
    if len(dataPoints) == 1:
        return dataPoints[0]

    # numIter depends on how long it take to get a suitable convergence of objFunc
    numIter = 50
    testMedian = candMedian(dataPoints)

    #minimise the objective function.
    for x in range(0,numIter):
        # print objfunc(testMedian,dataPoints)
        denom = denomsum(testMedian,dataPoints)
        nextx = 0.0
        nexty = 0.0

        for y in range(0,len(dataPoints)):
            nextx += (dataPoints[y][0] * numersum(testMedian,dataPoints[y]))/denom
            nexty += (dataPoints[y][1] * numersum(testMedian,dataPoints[y]))/denom

        testMedian = [nextx,nexty]

    app.logger.debug(testMedian)
    return testMedian
##################################################

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
        output.close()

def enum(**enums):
    return type('Enum', (), enums)

GraphLevelType = enum(layers=1, num_votes=2, flat=3)

QuestionPhaseType = enum(writing=1, voting=2, archive=3)

map_path = app.config['MAP_PATH']
work_file_dir = app.config['WORK_FILE_DIRECTORY']

def get_timestamp():
    return int(math.floor(time.time()))

def hash_string(str):
    '''
        .. function:: hash_string(str)

        Create the md5 hash of a string.

        :param question: str
        :type question: string
        :rtype: String
        '''
    import hashlib
    m = hashlib.md5()
    m.update(str)
    return m.hexdigest()

def make_new_map_filename_hashed(question,
                                 generation=None,
                                 algorithm=None):
    '''
        .. function:: make_new_map_filename_hashed(
            question[,
            generation=None,
            algorithm=None])

        Create the hash filname for the voting map.

        :param question: question
        :type question: Qustion
        :param generation: generation of the voting map
        :type generation: int
        :param algorithm: algorithm version number
        :type algorithm: int
        :rtype: String
        '''
    algorithm = algorithm or app.config['ALGORITHM_VERSION']
    generation = generation or question.generation
    import hashlib, json, pickle
    from flask import jsonify
    m = hashlib.md5()
    m.update(str(question.id) + str(generation))
    m.update(str(app.config['ANONYMIZE_GRAPH']))
    m.update(str(algorithm))
    all_endorsers = question.get_proposal_endorsers(generation)
    # app.logger.debug('*******************make_map_filename_hashed::proposal_endorsers ==> %s', proposal_endorsers)
    # app.logger.debug('make_map_filename_hashed::json ==> %s', json.dumps(proposal_endorsers))
    m.update(json.dumps(all_endorsers))
    return m.hexdigest()

def make_map_filename_hashed(question,
                             generation=None,
                             map_type="all",
                             proposal_level_type=GraphLevelType.layers,
                             user_level_type=GraphLevelType.layers,
                             algorithm=None):
    '''
        .. function:: make_map_filename_hashed(
            question[,
            generation,
            map_type="all",
            proposal_level_type=GraphLevelType.layers,
            user_level_type=GraphLevelType.layers,
            algorithm=None])

        Create the filname for the voting map.

        :param question: question
        :type question_id: Question
        :param generation: generation of the voting map
        :type generation: int
        :param map_type: map type
        :type map_type: string
        :param proposal_level_type: GraphLevelType
        :type proposal_level_type: GraphLevelType
        :param user_level_type: GraphLevelType
        :type user_level_type: GraphLevelType
        :param algorithm: algorithm version number
        :type algorithm: int
        :rtype: String
        '''
    algorithm = algorithm or app.config['ALGORITHM_VERSION']
    generation = generation or question.generation
    import hashlib, json, pickle
    from flask import jsonify
    m = hashlib.md5()
    m.update(str(question.id) + str(generation) + map_type)
    m.update(str(proposal_level_type) + str(user_level_type))
    m.update(str(app.config['ANONYMIZE_GRAPH']))
    m.update(str(algorithm))
    all_endorsers = question.get_proposal_endorsers(generation)
    # app.logger.debug('*******************make_map_filename_hashed::proposal_endorsers ==> %s', proposal_endorsers)
    # app.logger.debug('make_map_filename_hashed::json ==> %s', json.dumps(proposal_endorsers))
    m.update(json.dumps(all_endorsers))
    return m.hexdigest()

def make_map_filename(question_id,
                      generation,
                      map_type="all",
                      proposal_level_type=GraphLevelType.layers,
                      user_level_type=GraphLevelType.layers):
    '''
        .. function:: make_map_filename(
            question_id,
            generation[,
            map_type="all",
            proposal_level_type=GraphLevelType.layers,
            user_level_type=GraphLevelType.layers])

        Create the filname for the voting map.

        :param question_id: question id
        :type question_id: int
        :param generation: generation of the voting map
        :type generation: int
        :param map_type: map type
        :type map_type: string
        :param proposal_level_type: GraphLevelType
        :type proposal_level_type: GraphLevelType
        :type user_level_type: GraphLevelType
        :param user_level_type: GraphLevelType
        :rtype: String
        '''
    return "map" + "_Q" + str(question_id) + "_G" + \
           str(generation) + "_" + str(map_type) + \
           "_" + str(proposal_level_type) + \
           "_" + str(user_level_type)


# Proposal comments supported by a user
user_comments = db.Table(
    'user_comments',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('comment_id', db.Integer, db.ForeignKey('comment.id')))


#
# Useful Functions
#
def get_ids_from_proposals(proposals): # fix?
    ids = set()
    for prop in proposals:
        ids.add(prop.id)
    return ids


def get_ids_as_string_from_proposals(proposals): # fix?
    proposal_ids = get_ids_from_proposals(proposals)
    return '(' + ', '.join(str(id) for id in proposal_ids) + ')'


class Update(db.Model):
    '''
    Stores user question subscription data
    '''

    __tablename__ = 'update'

    def get_public(self):
        '''
        .. function:: get_public()

        Return public propoerties as string values for REST responses.

        :rtype: dict
        '''
        return {'question_id': str(self.question_id),
                'how': self.how,
                'last_update': str(self.last_update),
                'url': url_for('api_get_user_subscriptions',
                               user_id=self.user_id,
                               question_id=self.question_id)}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    how = db.Column(db.Enum('daily', 'weekly', 'asap', name="update_method_enum"))
    last_update = db.Column(db.DateTime)
    # M:1
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))

    subscribed_to = db.relationship("Question",
                                    backref="subscriber_update")

    def __init__(self, subscriber, subscribed_to, how=None):
        self.user_id = subscriber.id
        self.question_id = subscribed_to.id
        self.how = how or 'asap'


class User(db.Model, UserMixin):
    '''
    Stores the user data
    '''

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120), nullable=False)
    registered = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)

    # 1:M
    questions = db.relationship('Question', backref='author', lazy='dynamic',
                                cascade="all, delete-orphan")

    proposals = db.relationship('Proposal', backref='author', lazy='dynamic',
                                cascade="all, delete-orphan")

    endorsements = db.relationship('Endorsement',
                                   primaryjoin="User.id==Endorsement.user_id",
                                   backref='endorser', lazy='dynamic',
                                   cascade="all, delete-orphan")

    # updates 1:M
    subscribed_questions = db.relationship("Update", backref='subscriber',
                                           lazy='dynamic',
                                           cascade="all, delete-orphan")

    # invites M:M
    invites = db.relationship("Invite",
                              primaryjoin="User.id==Invite.sender_id",
                              backref="sender", lazy='dynamic',
                              cascade="all, delete-orphan")

    invites_received = db.relationship("Invite",
                              primaryjoin="User.id==Invite.receiver_id",
                              backref="owner", lazy='dynamic',
                              cascade="all, delete-orphan")

    # invites M:M
    invites_sent = db.relationship("UserInvite",
                              primaryjoin="User.id==UserInvite.sender_id",
                              backref="sender", lazy='dynamic',
                              cascade="all, delete-orphan")

    new_invites = db.relationship("UserInvite",
                              primaryjoin="User.id==UserInvite.receiver_id",
                              backref="invited", lazy='dynamic',
                              cascade="all, delete-orphan")

    comments = db.relationship(
        'Comment',
        secondary=user_comments,
        primaryjoin="user_comments.c.user_id == User.id",
        backref=db.backref('supporters', lazy='dynamic'),
        lazy='dynamic')

    def get_public(self):
        '''
        .. function:: get_public()

        Return public propoerties as string values for REST responses.

        :rtype: dict
        '''
        avatar_url = self.get_avatar()
        return {'id': str(self.id),
                'username': self.username,
                "registered": str(self.registered),
                "last_seen": str(self.last_seen),
                'url': url_for('api_get_users', user_id=self.id),
                'avatar_url': app.config['PROTOCOL'] + os.path.join(app.config['SITE_DOMAIN'], avatar_url)}

    def get_auth_token(self):
        """
        Encode a secure token for cookie
        """
        data = [str(self.id), self.password]
        from .auth import login_serializer
        return login_serializer.dumps(data)
    
    @staticmethod
    def get(userid):
        return User.query.filter_by(id=userid).first()

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
        self.registered = datetime.datetime.utcnow()
        self.last_seen = datetime.datetime.utcnow()
    
    @staticmethod
    def get_default_avatar():
        avatar = ''
        current_dir = os.path.dirname(os.path.realpath(__file__))
        app.logger.debug("current_dir => %s", current_dir)
        test_default_avatar_path = os.path.join(current_dir, app.config['UPLOADED_AVATAR_DEST'], 'default', '*')
        files = glob.glob(test_default_avatar_path)
        if len(files) > 0:
            avatar = os.path.join(app.config['UPLOADED_AVATAR_DEST'], 'default', os.path.basename(files[0]))
        return avatar

    def set_avatar(self, avatar):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        avatar_path = os.path.join(current_dir, app.config['UPLOADED_AVATAR_DEST'], str(self.id))
        app.logger.info("avatar path = %s", avatar_path)
        if not os.path.exists(avatar_path):
            try:
                os.makedirs(avatar_path)
            except IOError:
                app.logger.debug('Failed to create map path %s', avatar_path)
                return False
        else:
            app.logger.info("deleting current file in avatar path = %s", os.path.join(avatar_path, '*'))
            test_user_avatar_path = os.path.join(current_dir, app.config['UPLOADED_AVATAR_DEST'], str(self.id), '*')
            files = glob.glob(test_user_avatar_path)
            os.remove(files[0])

        from werkzeug import secure_filename
        filename = secure_filename(avatar.filename)
        fix_filename = os.path.splitext(filename)
        avatar.filename = hash_string(filename) + fix_filename[1]
        app.logger.debug("Saving avatar to %s", os.path.join(avatar_path, avatar.filename))
        avatar.save(os.path.join(avatar_path, avatar.filename))
        if not os.path.isfile(os.path.join(avatar_path, avatar.filename)):
            return False
        else:
            return os.path.join(app.config['UPLOADED_AVATAR_DEST'], str(self.id), avatar.filename)
    
    def get_avatar(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        avatar = ''
        test_user_avatar_path = os.path.join(current_dir, app.config['UPLOADED_AVATAR_DEST'], str(self.id), '*')
        app.logger.debug("test_user_avatar_path = %s", test_user_avatar_path)
        files = glob.glob(test_user_avatar_path)
        app.logger.debug("test_user_avatar_path = %s", files)
        if len(files) > 0:
            avatar = os.path.join(app.config['UPLOADED_AVATAR_DEST'], str(self.id), os.path.basename(files[0]))
        else:
            avatar = User.get_default_avatar()
        return avatar

    def support_comment(self, comment):
        '''
        .. function:: support_comments(comments)

        Get all comments for a particular generation of the propsal.

        :param comments: list of comments to support
        :type comments: list
        :rtype: None
        '''
        self.comments.append(comment)

    def get_uninvited_associated_users(self, question): # arse
        '''
        .. function:: get_uninvited_associated_users()

        Get all users who participated in OTHER questions also participated in
        by this user.

        :rtype: list
        '''
        invited_uids = set()
        current_invites = question.invites.all()
        for invite in current_invites:
            invited_uids.add(invite.receiver_id)
        new_invites = question.invites_sent.all()
        for invite in new_invites:
            invited_uids.add(invite.receiver_id)
        
        invited_uids = list(invited_uids)
        
        questions_participated = db_session.query(Invite.question_id)\
            .filter(Invite.receiver_id == self.id)\
            .all()

        qids = set()
        for item in questions_participated:
            qids.add(item[0])
        qids = list(qids)
        
        associates = db_session.query(Invite.receiver_id)\
            .filter(Invite.question_id.in_(qids))\
            .filter(Invite.receiver_id != self.id)\
            .filter(not_(Invite.receiver_id.in_(invited_uids)))\
            .all()
        
        uids = set()
        for user in associates:
            uids.add(user[0])
                
        uids = list(uids)
        users = db_session.query(User)\
            .filter(User.id.in_(uids))\
            .all()
        
        uninvited_associates = list()
        for user in users:
            uninvited_associates.append({'username': user.username, 'user_id': user.id})
        
        return uninvited_associates

    def get_associated_users(self, ignore_question_id=None):
        '''
        .. function:: get_associated_users()

        Get all users who participated in OTHER questions also participated in
        by this user.

        :rtype: list
        '''
        '''
        invitations = self.invites_received.\
        filter(Invite.question_id != ignore_question_id).\
        all()
        '''
        invitations_query = self.invites_received
        
        #if ignore_question_id:
        #invitations_query.filter(Invite.question_id != ignore_question_id)
        
        #invitations = invitations_query.all()
        
        # current_participants = 
        
        invitations = db_session.query(Invite).\
            filter(Invite.question_id != ignore_question_id).\
            filter(Invite.sender_id != self.id).\
            all()
        
        
        #return invitations

        qids = set()
        for invite in invitations:
            qids.add(invite.question_id)

        #return qids
        
        associate_invites = db_session.query(Invite).\
                filter(Invite.question_id.in_(qids)).\
                filter(Invite.receiver_id != self.id).\
                group_by(Invite.receiver_id).\
                all()

        associates = list()
        for invite in associate_invites:
            associates.append({'username': invite.receiver.username, 'user_id': invite.receiver_id})
        return associates

    def get_question_permission(self, question):
        invite = self.invites_received.filter(Invite.question_id == question.id).first()
        if invite:
            return invite.permissions
        else:
            return False
    
    def get_endorsement_count(self, question, generation=None):
        '''
        .. function:: get_endorsement_count(question[, generation=None])

        Get endorsement count for the generation of a question.

        :param question: question
        :type question: int
        :rtype: boolean
        '''
        generation = generation or question.generation
        return db_session.query(Endorsement)\
                        .filter(Endorsement.user_id == self.id)\
                        .filter(Endorsement.question_id == question.id)\
                        .filter(Endorsement.generation == generation)\
                        .count()

    def generations_participated_count(self, question):
        '''
        .. function:: get_endorsement_count(question[, generation=None])

        Get endorsement count for the generation of a question.

        :param question: question
        :type question: int
        :rtype: boolean
        '''
        return db_session.query(distinct(Endorsement.generation))\
                        .filter(Endorsement.question_id == question.id)\
                        .count()

    def unsupport_comment(self, comment):
        '''
        .. function:: unsupport_comments(comments)

        Get all comments for a particular generation of the propsal.

        :param comments: list of comments to stop supporting
        :type comments: list
        :rtype: None
        '''
        self.comments.remove(comment)
    
    def support_comments(self, comments):
        '''
        .. function:: support_comments(comments)

        Get all comments for a particular generation of the propsal.

        :param comments: list of comments to support
        :type comments: list
        :rtype: None
        '''
        if (comments):
            for comment in comments:
                self.comments.append(comment)

    def unsupport_comments(self, comments):
        '''
        .. function:: unsupport_comments(comments)

        Get all comments for a particular generation of the propsal.

        :param comments: list of comments to stop supporting
        :type comments: list
        :rtype: None
        '''
        if (comments):
            for comment in comments:
                self.comments.remove(comment)

    def get_supported_comments(self, proposal, generation=None):
        '''
        .. function:: get_supported_comments(proposal[, generation=None])

        Get all proposl comments supported by this user.

        :param proposal: proposal
        :type proposal: Proposal
        :param generation: proposal generation, defaults to current
        :type generation: int
        :rtype: list
        '''
        generation = generation or proposal.question.generation
        return self.comments.filter(and_(
            Comment.proposal_id == proposal.id,
            Comment.generation == generation)).all()

    def get_active_questions(self): # shark
        '''
        .. function:: get_active_questions()

        Get all questions for this user for which he has permission,
        either through being the author or through having been invited.

        :rtype: list
        '''
        return db_session.query(Question).join(Invite).\
            filter(Question.id == Invite.question_id).\
            filter(Invite.receiver_id == self.id).\
            all()

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

    def invite_all(self, receivers, permissions, question):
        # Only author can invite to own question and cannot invite himself
        '''
        .. function:: invite(receiver, question)

        Create invitations to request the receivers participate
        in the question.

        :param receivers: the users to be invited
        :type receiver: List
        :param question: the author's question
        :type question: Question
        :rtype: boolean
        '''
        if (self.id == question.author.id and self.id not in receivers):
            for receiver_id in receivers:
                receiver = User.query.get(receiver_id)
                if not receiver:
                    continue
                else:
                    app.logger.debug('appending invite for user id %s', receiver)
                    self.invites_sent.append(UserInvite(self, receiver, permissions, question.id))
                    # send email notification to receiver
                    emails.send_added_to_question_email(self, receiver, question)
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

    def get_endorsed_proposal_ids_2(self, question, proposals, generation=None):
        '''
        .. function:: get_endorsed_proposal_ids(question[, generation=None])

        Fetch a set of the IDs of the proposals endorsed by the
        user for this generation of this question.

        :param question: associated question
        :type question: Question
        :param generation: question generation
        :type generation: int or None
        :rtype: set
        '''
        generation = generation or question.generation
        map_proposal_ids = get_ids_from_proposals(proposals)

        endorsements = self.endorsements.join(User.endorsements).\
            join(Endorsement.proposal).filter(and_(
                Endorsement.user_id == self.id,
                Proposal.question_id == question.id,
                Endorsement.generation == generation,
                Endorsement.endorsement_type == 'endorse')
            ).all()
        proposal_ids = set()
        for endorsement in endorsements:
            proposal_ids.add(endorsement.proposal_id)
        # Return the ids of the endorsed proposals within the intersection
        return proposal_ids & map_proposal_ids

    def get_endorsed_proposal_ids(self, question, generation=None):
        '''
        .. function:: get_endorsed_proposal_ids(question[, generation=None])

        Fetch a set of the IDs of the proposals endorsed by the
        user for this generation of this question.

        :param question: associated question
        :type question: Question
        :param generation: question generation
        :type generation: int or None
        :rtype: set
        '''
        generation = generation or question.generation

        endorsements = self.endorsements.join(User.endorsements).\
            join(Endorsement.proposal).filter(and_(
                Endorsement.user_id == self.id,
                Proposal.question_id == question.id,
                Endorsement.generation == generation,
                Endorsement.endorsement_type == 'endorse')
            ).all()
        proposal_ids = set()
        for endorsement in endorsements:
            proposal_ids.add(endorsement.proposal_id)
        return proposal_ids

    def get_endorsed_proposal_ids_new(self, question, generation=None, all_proposal_ids=None):
        '''
        .. function:: get_endorsed_proposal_ids(question[, generation=None])

        Fetch a set of the IDs of the proposals endorsed by the
        user for this generation of this question.

        :param question: associated question
        :type question: Question
        :param generation: question generation
        :type generation: int or None
        :rtype: set
        '''
        generation = generation or question.generation

        endorsements = self.endorsements.join(User.endorsements).\
            join(Endorsement.proposal).filter(and_(
                Endorsement.user_id == self.id,
                Proposal.question_id == question.id,
                Endorsement.generation == generation,
                Endorsement.endorsement_type == 'endorse')
            ).all()

        proposal_ids = set()
        if all_proposal_ids:
            for endorsement in endorsements:
                if endorsement.proposal_id in all_proposal_ids:
                    proposal_ids.add(endorsement.proposal_id)
            return proposal_ids
        else:
            for endorsement in endorsements:
                proposal_ids.add(endorsement.proposal_id)
            return proposal_ids

    def get_all_endorsememnts(self, question, generation=None):
        '''
        .. function:: get_all_endorsememnts(question[, generation=None])

        Fetch a list of this user's endorsements for a question.

        :param question: question
        :type question: Question object
        :param generation: question generation
        :type generation: int or None
        :rtype: list of proposals
        '''
        generation = generation or question.generation
        all_votes = self.endorsements.filter(Endorsement.question_id == question.id,
                                             Endorsement.generation == generation).all()
        return all_votes

    def get_all_endorsememnts_for(self, question, proposal_ids, generation=None):
        '''
        .. function:: get_all_endorsememnts(question[, generation=None])

        Fetch a list of this user's endorsements for a question.

        :param question: question
        :type question: Question object
        :param generation: question generation
        :type generation: int or None
        :rtype: list of proposals
        '''
        generation = generation or question.generation
        all_votes = self.endorsements.filter(Endorsement.proposal_id.in_(x for x in proposal_ids),
                                             Endorsement.generation == generation).all()
        return all_votes
    
    def get_endorsed_proposals(self, question, generation=None):
        '''
        .. function:: get_endorsed_proposals(question[, generation=None])

        Fetch a LIST of the proposals endorsed by the
        user for this generation of this question.

        :param question: question
        :type question: Question object
        :param generation: question generation
        :type generation: int or None
        :rtype: list of proposals
        '''
        generation = generation or question.generation

        endorsements = self.endorsements.join(User.endorsements).\
            join(Endorsement.proposal).filter(and_(
                Endorsement.user_id == self.id,
                Proposal.question_id == question.id,
                Endorsement.generation == generation,
                Endorsement.endorsement_type == 'endorse')
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
        :type generation: int or None
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
        :type generation: int or None
        :rtype: list of proposals
        '''
        generation = generation or question.generation

        proposals = self.get_proposals(question, generation)

        proposal_ids = list()
        for proposal in proposals:
            proposal_ids.append(proposal.id)
        return proposal_ids

    def get_all_proposals(self, question, generation=None): # jazz
        '''
        .. function:: get_proposals(question[, generation=None])

        Fetch a LIST of the proposals authored by the user for this question.

        :param question: associated question
        :param generation: question generation
        :type generation: int or None
        :rtype: list of proposals
        '''
        '''
        return self.proposals.filter(and_(
            Proposal.question == question,
            Proposal.generation == generation)
        ).all()
        '''
        generation = generation or question.generation

        return db_session.query(Proposal).join(QuestionHistory).\
            filter(QuestionHistory.question_id == question.id).\
            filter(QuestionHistory.generation == generation).\
            filter(Proposal.user_id == self.id).\
            all()

    def get_proposals(self, question, generation=None):
        '''
        .. function:: get_proposals(question[, generation=None])

        Fetch a LIST of the proposals authored by the user for this question.

        :param question: associated question
        :param generation: question generation
        :type generation: int or None
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
            filter(QuestionHistory.user_id == self.id).\
            all()

    def delete_proposal(self, prop):
        '''
        .. function:: delete_proposal(prop)

        Delete the user's proposal.
        Users can only delete their new proposals during the writing phase
        of the generation in which the proposal is created.

        :param prop: the proposal object to delete
        :rtype: boolean
        '''
        proposal = self.proposals.filter(and_(
            Proposal.id == prop.id,
            Proposal.user_id == self.id
        )).first()
        app.logger.debug("delete_proposal: Found: %s\n",
                         proposal)
        if proposal is not None \
                and proposal.question.phase == 'writing' \
                and proposal.question.generation == proposal.generation_created:
            app.logger.debug("Removing proposal.....\n")
            # Delete entry from QuestionHistory table or not ???
            self.proposals.remove(proposal)
            return True
        else:
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

        Checks if the user is subscribed to the question.

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

    def __repr__(self):
        return "<User(ID='%s', '%s')>" % (self.id,
                                          self.username)

class VerifyEmail(db.Model):
    '''
    Stores record of a users email verification data
    '''
    __tablename__ = 'verify_email'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    email = db.Column(db.String(120))
    token = db.Column(db.String(32), unique=True)
    email_sent = db.Column(db.Boolean, unique=False, default=False)
    timeout = db.Column(db.Integer)

    user = db.relationship("User",
                            primaryjoin="VerifyEmail.user_id==User.id",
                            backref="verify_email",
                            lazy='static', single_parent=True)

    def __init__(self, user, email, token, timeout):
        self.user_id = user.id
        self.email = email
        self.token = token
        self.timeout = timeout
    
    @staticmethod
    def verified(verify):
        app.logger.debug("verified called...\n")
        db_session.delete(verify)
        db_session.commit()
    
    @staticmethod
    def verify_email(user_id, token):
        app.logger.debug("verify_email called...\n")

        verify = VerifyEmail.query.filter_by(user_id=user_id,token=token).first()

        if not verify:
            app.logger.debug("Token and user_id not listed...\n")
            return False

        elif get_timestamp() > verify.timeout:
            app.logger.debug("Token expired...\n")
            return False

        user =  User.query.get(verify.user_id)
        if not user:
            app.logger.debug("Unknown user...\n")
            return False
    
        auth_token = user.get_auth_token()
        return auth_token

class EmailInvite(db.Model):
    '''
    Stores users email invitaions to participate in questions
    '''
    __tablename__ = 'email_invite'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_email = db.Column(db.String(120))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    permissions = db.Column(db.Integer, default=1)
    token = db.Column(db.String(32), unique=True)
    email_sent = db.Column(db.Boolean, unique=False, default=False)
    accepted = db.Column(db.Boolean, unique=False, default=False)
    
    sender = db.relationship("User",
                             primaryjoin="EmailInvite.sender_id==User.id",
                             backref="email_invites_sent",
                             lazy='static', single_parent=True)

    def get_public(self):
        '''
        .. function:: get_public()

        Return public propoerties as string values for REST responses.

        :rtype: dict
        '''
        return {'id': str(self.id),
                'sender_id': self.sender_id,
                'receiver_email': self.receiver_email,
                'question_id': self.question_id,
                'permissions': self.permissions,
                'sender_url': url_for('api_get_users',
                                      user_id=self.sender_id)}
                
    def __init__(self, sender, receiver_email, permissions, question_id, token):
        self.sender_id = sender.id
        self.question_id = question_id
        self.permissions = permissions
        self.receiver_email = receiver_email
        self.token = token

    @staticmethod
    def check_token(token):
        email_invitation = db_session.query(EmailInvite)\
            .filter(and_(EmailInvite.accepted == 0, EmailInvite.token == token))\
            .first()
        if not email_invitation:
            app.logger.debug("add_invitation_from_token Token not found: %s", token)
            return False
        else:
            return True
    
    @staticmethod
    def accept(user, token):
        email_invitation = db_session.query(EmailInvite)\
            .filter(and_(EmailInvite.accepted == 0, EmailInvite.token == token))\
            .first()
        if not email_invitation:
            app.logger.debug("add_invitation_from_token Token not found: %s", token)
            return False

        app.logger.debug("Invitation found from %s", email_invitation.sender_id)

        sender = User.query.get(email_invitation.sender_id)
        if not sender:
            app.logger.debug("add_invitation_from_token Sender not found with ID: %s", email_invitation.sender_id)
            return False

        question = Question.query.get(email_invitation.question_id)
        if not question:
            app.logger.debug("add_invitation_from_token question not found with ID: %s", email_invitation.question_id)
            return False

        # Check if user is already added to the question
        already_added = db_session.query(Invite)\
                .filter(Invite.question_id == question.id)\
                .filter(Invite.receiver_id == user.id)\
                .all()

        # Add invite, mark email_invitation as accepted and open question page
        #
        # First check that user not already invited
        if not already_added:
            invite = Invite(sender, user, email_invitation.permissions, email_invitation.question_id)
            app.logger.debug("Invite from %s for %s", invite.sender_id, invite.question_id)
            email_invitation.accepted = 1
            user.invites_received.append(invite)
            # Notify sender
            app.logger.debug('Send sender %s a email_invite_accepted_email to %s...', sender.username, sender.email)
            emails.send_email_invite_accepted_email(sender, email_invitation.receiver_email, question)
        # Otherwise noify sender of prior acceptance or earlier invitation
        else:
            app.logger.debug('Send sender %s a user_already_added_email to %s...', sender.username, sender.email)
            emails.send_user_already_added_email(sender, email_invitation.receiver_email, question)

        # Delete email invite
        db_session.delete(email_invitation)
        db_session.commit()

        return question.id


class UserInvite(db.Model):
    '''
    Stores users invitaions to participate in questions
    '''
    __tablename__ = 'user_invite'

    def get_public(self):
        '''
        .. function:: get_public()

        Return public propoerties as string values for REST responses.

        :rtype: dict
        '''
        return {'id': self.id,
                'sender_id': self.sender_id,
                'sender_username': self.sender.username,
                'receiver_id': self.receiver_id,
                'question_id': self.question_id,
                'question_title': self.question.title,
                'permissions': self.permissions,
                'sender_url': url_for('api_get_users',
                                      user_id=self.sender_id)}

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    permissions = db.Column(db.Integer, default=1)

    receiver = db.relationship("User",
                               primaryjoin="UserInvite.receiver_id==User.id",
                               backref="new_invitations",
                               lazy='static', single_parent=True)


    def __init__(self, sender, receiver, permissions, question_id):
        self.sender_id = sender.id
        self.question_id = question_id
        self.permissions = permissions

        if isinstance(receiver, (int, long)):
            self.receiver_id = receiver
        else:
            self.receiver_id = receiver.id

class Invite(db.Model):
    '''
    Stores users invitaions to participate in questions
    '''
    __tablename__ = 'invite'

    def get_public(self):
        '''
        .. function:: get_public()

        Return public propoerties as string values for REST responses.

        :rtype: dict
        '''
        return {'id': str(self.id),
                'sender_id': self.sender_id,
                'receiver_id': self.receiver_id,
                'question_id': self.question_id,
                'permissions': self.permissions,
                'sender_url': url_for('api_get_users',
                                      user_id=self.sender_id),
                'receiver_id': url_for('api_get_users',
                                       user_id=self.receiver_id)}

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    permissions = db.Column(db.Integer, default=1)

    receiver = db.relationship("User",
                               primaryjoin="Invite.receiver_id==User.id",
                               backref="invitations",
                               lazy='static', single_parent=True)

    def __init__(self, sender, receiver, permissions, question_id):
        self.sender_id = sender.id
        self.question_id = question_id
        self.permissions = permissions

        if isinstance(receiver, (int, long)):
            self.receiver_id = receiver
        else:
            self.receiver_id = receiver.id


class PWDReset(db.Model):
    '''
    Stores data for password reset requests.
    '''

    __tablename__ = 'pwd_reset'

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    token = db.Column(db.String(32), unique=True)
    timeout = db.Column(db.Integer)

    def __init__(self, user, token, timeout):
        '''
        .. function:: __init__(user, token, timeout)

        Creates a PWDReset object.

        :param user: user
        :type user: User
        :param token: unique reset token
        :type token: string
        :param timeout: timestamp to expire token
        :type timeout: integer
        '''
        self.user_id = user.id
        self.email = user.email
        self.token = token
        self.timeout = timeout
    
    @staticmethod
    def get_user_from_password_reset_token(token):
        app.logger.debug("submit_password_reset_token called...\n")

        pwd_reset = db_session.query(PWDReset)\
            .filter(PWDReset.token == token)\
            .first()

        if not pwd_reset:
            app.logger.debug("Token %s not listed...\n", token)
            return False

        elif get_timestamp() > pwd_reset.timeout:
            app.logger.debug("Token expired...\n")
            return False

        return User.query.get(pwd_reset.user_id)


    @staticmethod
    def submit_password_reset_token(token):
        app.logger.debug("submit_password_reset_token called...\n")

        pwd_reset = PWDReset.query.filter_by(token=token).first()

        if not pwd_reset:
            app.logger.debug("Token and user_id not listed...\n")
            return False

        elif get_timestamp() > pwd_reset.timeout:
            app.logger.debug("Token expired...\n")
            return False

        user =  User.query.get(pwd_reset.user_id)
        if not user:
            app.logger.debug("Token expired...\n")
            return False
    
        auth_token = user.get_auth_token()
        return auth_token

class Question(db.Model):
    '''
    Stores data and handles functionality and relations for
    the question object.
    '''

    __tablename__ = 'question'

    def __repr__(self):
        return "<Question(%s '%s' by %s - Gen %s - %s)>" % (self.id,
                                                       self.title,
                                                       self.author.username,
                                                       self.generation,
                                                       self.phase)

    # User question permissions
    READ = 1
    VOTE = 2
    PROPOSE = 4
    INVITE = 8
    # Combined
    VOTE_READ = 3
    PROPOSE_READ = 5
    VOTE_PROPOSE_READ = 7
    
    def get_public(self, user=None):
        '''
        .. function:: get_public()

        Return public propoerties as string values for REST responses.

        :rtype: dict
        '''
        # Fetch current threshold coordinates for this generation
        from sqlalchemy.orm.exc import NoResultFound
        try:
            threshold = self.thresholds\
                .filter(Threshold.generation == self.generation).first()
        except NoResultFound, e:
            print "No threshold found for question " + str(self.id) + ' gen ' + str(self.generation)
            raise

        inherited_proposal_count = self.get_inherited_proposal_count()
        #consensus_found = (inherited_proposal_count == 1) and (self.get_new_proposal_count() == 0)
        consensus_found = self.consensus_found(generation=self.generation-1)
        completed_voter_count = self.get_completed_voter_count(generation=self.generation)
        voters_voting_count = self.get_voters_voting_count()

        public = {'id': str(self.id),
                'url': url_for('api_get_questions', question_id=self.id),
                'title': self.title,
                'blurb': self.blurb,
                'room': self.room,
                'generation': str(self.generation),
                'created': str(self.created),
                "last_move_on": str(self.last_move_on),
                "minimum_time": str(self.minimum_time),
                "maximum_time": str(self.maximum_time),
                'phase': self.phase,
                'author': self.author.username,
                'avatar_url': app.config['PROTOCOL'] + os.path.join(app.config['SITE_DOMAIN'], self.author.get_avatar()),
                'author_id': self.author.id,
                'proposal_count': str(self.get_proposal_count()),
                'new_proposal_count': str(self.get_new_proposal_count()),
                'new_proposer_count': str(self.get_new_proposer_count()),
                'participant_count': str(self.invites.count()),
                'consensus_found': consensus_found,
                'inherited_proposal_count' : str(inherited_proposal_count),
                'author_url': url_for('api_get_users', user_id=self.user_id),
                'mapx': str(threshold.mapx),
                'mapy': str(threshold.mapy),
                'completed_voter_count': str(completed_voter_count),
                'voters_voting_count': str(voters_voting_count)}

        # Add user permissions
        permissions = None
        if user:
            permissions = self.get_permissions(user)
            
            # Add participant permissions if user is question author
            
            if user.id == self.author.id:
                user_permissions = self.get_participant_permissions()
                if user_permissions:
                    public['user_permissions'] = user_permissions
                else:
                    public['user_permissions'] = list()
            

        if permissions:
            public['can_vote'] = bool(Question.VOTE & permissions)
            public['can_propose'] = bool(Question.PROPOSE & permissions)
        else:
            public['can_vote'] = False
            public['can_propose'] = False

        return public

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    blurb = db.Column(db.Text, nullable=False)
    generation = db.Column(db.Integer, default=1, nullable=False)
    room = db.Column(db.String(30))
    phase = db.Column(db.Enum('writing', 'voting', 'archived', 'consensus', 'results', name="question_phase_enum"),
                      default='writing')
    # created = db.Column(db.DateTime)
    # last_move_on = db.Column(db.DateTime)
    created = db.Column(db.Integer)
    last_move_on = db.Column(db.Integer)
    minimum_time = db.Column(db.Integer)
    maximum_time = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    proposals = db.relationship('Proposal', backref='question', lazy='dynamic',
                                cascade="all, delete-orphan")
    history = db.relationship('QuestionHistory', lazy='dynamic',
                              cascade="all, delete-orphan")
    key_players = db.relationship('KeyPlayer', lazy='dynamic',
                                  cascade="all, delete-orphan")
    thresholds = db.relationship('Threshold', lazy='dynamic',
                              cascade="all, delete-orphan")
    invites = db.relationship('Invite', lazy='dynamic', backref='question',
                              primaryjoin="Invite.question_id == Question.id",
                              cascade="all, delete-orphan")
    email_invites = db.relationship('EmailInvite', lazy='dynamic', backref='question',
                              primaryjoin="EmailInvite.question_id == Question.id",
                              cascade="all, delete-orphan")
    invites_sent = db.relationship('UserInvite', lazy='dynamic', backref='question',
                              primaryjoin="UserInvite.question_id == Question.id",
                              cascade="all, delete-orphan")

    def __init__(self, author, title, blurb,
                 minimum_time=86400, maximum_time=604800, room=None):
        '''
        .. function:: __init__(author, title, blurb
                [, minimum_time=86400, maximum_time=604800, room=None])

        Creates a Question object.

        :param author: question author
        :type author: User
        :param title: question title
        :type title: string
        :param blurb: uestion content
        :type blurb: string
        :param minimum_time: minimum time before a question can be moved on
        :type minimum_time: int
        :param maximum_time: time until the author will be asked to move the question on
        :type maximum_time: int
        :param room: question room
        :type room: string
        '''
        self.user_id = author.id
        self.title = title
        self.blurb = blurb
        self.room = room or ''
        self.created = get_timestamp()
        self.last_move_on = get_timestamp()
        self.phase = 'writing'
        self.minimum_time = minimum_time
        self.maximum_time = maximum_time
    
    # sharks
    def get_not_invited(self):
        '''
        .. function:: get_not_invited()

        Get a list of details of users not yet invited to the question.

        :rtype: list
        '''
        
        '''
        SELECT `user`.id, `invite`.id FROM `user` 
        LEFT JOIN `invite` 
        ON user.id = invite.receiver_id 
        AND `invite`.question_id = 2 
        WHERE `invite`.id IS NULL
        ORDER BY `user`.id
        '''
        not_invited = db.session.query(User).\
            outerjoin(Invite, and_(Invite.receiver_id == User.id, Invite.question_id == self.id)).\
            filter(Invite.id == None).\
            all()
        
        app.logger.debug('not_invited ==> %s', not_invited)        
        
        users_to_invite = list()
        if not_invited is None:
            return users_to_invite
        else:
            for user in not_invited:
                users_to_invite.append({'username': user.username, 'user_id': user.id})
            return users_to_invite
    
    def get_participants(self):
        '''
        .. function:: get_participant_permissions()

        Get a question's participants.

        :rtype: list
        '''
        participants = list()
        invitations = self.invites.all()
        if not invitations is None:
            for invitation in invitations:
                user = User.query.get(invitation.receiver.id)
                if user:
                    participants.append(user)
        return participants
    
    def get_participant_permissions(self):
        '''
        .. function:: get_participant_permissions()

        Get a question's invitations and their associatd permissions.

        :rtype: list
        '''
        participants = list()
        invitations = self.invites.all()
        if not invitations is None:
            for invitation in invitations:
                participants.append({'username': invitation.receiver.username, 'user_id': str(invitation.receiver.id), 'permissions': str(invitation.permissions)})

        return participants
    
    def get_permissions(self, user):
        '''
        .. function:: get_permissions()

        Get user's permissions to access this question,
        granted either through being the author or through having been invited
        to participate.

        :rtype: Integer
        '''
        invite = self.invites.filter_by(receiver_id=user.id).first()
        if invite is None:
            return 0
        else:
            return invite.permissions

    def get_endorsement_results(self, generation=None): # final
        '''
        .. function:: get_endorsement_results([generation=None])

        Calculate the median x and y for all endorsements of all proposals for 
        this question.
        Takes an optional generation value to check historic endorsements.

        :param generation: question generation
        :type generation: int or None
        :rtype: dict
        '''
        generation = generation or self.generation

        app.logger.debug('get_endorsement_results called for generation %s', generation)

        voter_count = self.get_voter_count(generation)
        app.logger.debug("There were %s voters in generation %s", voter_count, generation)
        
        proposals = self.get_proposals_list_by_id()

        endorsements = db_session.query(Endorsement)\
                .filter(Endorsement.question_id == self.id)\
                .filter(Endorsement.generation == generation)\
                .all()

        if not endorsements:
            return dict()
        else:
            app.logger.debug("endorsements ==> %s", endorsements)
            
            endorsement_data = dict()
            for endorsement in endorsements:
                pid = endorsement.proposal_id
                if not pid in endorsement_data:
                    endorsement_data.update({pid: {'mapx': [endorsement.mapx], 
                                                   'mapy': [endorsement.mapy],
                                                   'voters': {endorsement.user_id: {'mapx': endorsement.mapx,
                                                                                    'mapy': endorsement.mapy,
                                                                                    'username' : endorsement.endorser.username}}}})
                else:
                    endorsement_data[pid]['mapx'].append(endorsement.mapx)
                    endorsement_data[pid]['mapy'].append(endorsement.mapy)
                    endorsement_data[pid]['voters'].update( {endorsement.user_id: {'mapx': endorsement.mapx,
                                                                                   'mapy': endorsement.mapy,
                                                                                   'username' : endorsement.endorser.username}} )

            app.logger.debug("endorsement_data ==> %s", endorsement_data)

            results = dict()
            for (pid, coords) in endorsement_data.iteritems():
                results.update( {pid: {'median': {'medx': median(coords['mapx']),
                                                  'medy': median(coords['mapy'])},
                                       'voters': coords['voters']} } )

                # Update DB with proposal medians
                geomedx = median(coords['mapx'])
                geomedy = median(coords['mapy'])
                proposals[pid].geomedx = geomedx
                proposals[pid].geomedy = geomedy

                '''
                1L: {'mapx': [0.75, 0.65, 0.631388, 0.497361, 0.428218], 'mapy': [0.46, 0.16, 0.634726, 0.598698, 0.710889]}
                '''
                # Add error triangle points
                not_voted = voter_count - len(coords['mapx'])
                if not_voted > 0:

                    app.logger.debug("Adding %s error points for pid %s", not_voted, pid)

                    results[pid]['o_error'] = {'mapx': median(coords['mapx'] + [0] * not_voted),
                                               'mapy': median(coords['mapy'] + [0] * not_voted)}
                    results[pid]['e_error'] = {'mapx': median(coords['mapx'] + [1] * not_voted),
                                               'mapy': median(coords['mapy'] + [0] * not_voted)}
                    results[pid]['c_error'] = {'mapx': median(coords['mapx'] + [0.5] * not_voted),
                                               'mapy': median(coords['mapy'] + [1] * not_voted)}

            # Add PF domination data == yelp
            history = self.get_history(generation=generation)
            for (proposal_id, data) in history.iteritems():
                if proposal_id in results:
                    results[proposal_id]['dominated_by'] = data.dominated_by

            app.logger.debug("results ==> %s", results)
            
            # Commit medians to DB
            db_session.commit()

            return results

    def consensus_found(self, algorithm=None):
        '''
        .. function:: consensus_found([generation=None])

        Returns true if a consensus was reached
        during the selected generation of the question.

        :param generation: question generation.
        :type generation: int
        :rtype: bool
        '''
        if self.phase == 'voting':
            return False
        elif self.generation == 1:
            return False
        elif self.get_new_proposer_count() > 0:
            return False
        # Find recent endorser count
        prev_generation = self.generation - 1
        recent_endorser_count = self.get_voter_count(prev_generation)
        # Get recent pareto
        recent_pareto = self.calculate_pareto_front(generation=prev_generation, algorithm=algorithm)
        for proposal in recent_pareto:
            if recent_endorser_count != proposal.get_endorser_count(generation=prev_generation):
                return False
        return True

    def get_voters_voting_count(self, generation=None):
        '''
        .. function:: get_voter_count([generation=None])

        Returns the number of people who participated in the voting round
        during the selected generation of the question.

        :param generation: question generation.
        :type generation: int
        :rtype: int
        '''
        generation = generation or self.generation
        num_proposals = self.get_proposal_count(generation)

        return db_session.query(func.count(Endorsement))\
        .filter(Endorsement.question_id == self.id)\
        .filter(Endorsement.generation == generation)\
        .group_by(Endorsement.user_id)\
        .having(func.count(Endorsement) >= 1)\
        .count()
    
    def get_completed_voter_count(self, generation=None):
        '''
        .. function:: get_voter_count([generation=None])

        Returns the number of people who participated in the voting round
        during the selected generation of the question.

        :param generation: question generation.
        :type generation: int
        :rtype: int
        '''
        generation = generation or self.generation
        num_proposals = self.get_proposal_count(generation)

        return db_session.query(func.count(Endorsement))\
        .filter(Endorsement.question_id == self.id)\
        .filter(Endorsement.generation == generation)\
        .group_by(Endorsement.user_id)\
        .having(func.count(Endorsement) == num_proposals)\
        .count()
    
    def get_voter_count(self, generation=None):
        '''
        .. function:: get_voter_count([generation=None])

        Returns the number of people who participated in the voting round
        during the selected generation of the question.

        :param generation: question generation.
        :type generation: int
        :rtype: int
        '''
        generation = generation or self.generation
        return db_session.query(distinct(Endorsement.user_id))\
                        .filter(Endorsement.question_id == self.id)\
                        .filter(Endorsement.generation == generation)\
                        .count()

    def get_all_proposals(self):
        return db_session.query(Proposal).join(QuestionHistory)\
                        .filter(QuestionHistory.question_id == self.id)\
                        .all()
    
    def get_inherited_proposals(self, generation=None):
        generation = generation or self.generation
        if generation == 1:
            return list()
        else:
            return db_session.query(Proposal).join(QuestionHistory)\
                        .filter(QuestionHistory.question_id == self.id)\
                        .filter(QuestionHistory.generation == generation)\
                        .filter(Proposal.generation_created < self.generation)\
                        .all()
    
    def get_inherited_proposal_count(self, generation=None):
        generation = generation or self.generation
        if generation == 1:
            return 0
        else:
            return db_session.query(Proposal).join(QuestionHistory)\
                        .filter(QuestionHistory.question_id == self.id)\
                        .filter(QuestionHistory.generation == generation)\
                        .filter(Proposal.generation_created < self.generation)\
                        .count()

    def get_new_proposal_count(self):
        return db_session.query(Proposal).join(QuestionHistory)\
                    .filter(QuestionHistory.question_id == self.id)\
                    .filter(QuestionHistory.generation == self.generation)\
                    .filter(Proposal.generation_created == self.generation)\
                    .count()

    def get_new_proposer_count(self):
        proposals = db_session.query(Proposal).join(QuestionHistory)\
                    .filter(QuestionHistory.question_id == self.id)\
                    .filter(QuestionHistory.generation == self.generation)\
                    .filter(Proposal.generation_created == self.generation)\
                    .all()
        proposers = set()
        for proposal in proposals:
            proposers.add(proposal.user_id)
        return len(proposers)

    def get_proposer_count(self, generation=None):
        generation = generation or self.generation
        proposals = self.get_proposals_list()
        proposers = set()
        for proposal in proposals:
            proposers.add(proposal.user_id)
        return len(proposers)

    def get_proposal_count(self, generation=None):
        generation = generation or self.generation
        return self.history\
            .filter(QuestionHistory.generation == generation)\
            .filter(QuestionHistory.question_id == self.id)\
            .count()

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

    def auto_move_on(self):
        '''
        .. function:: auto_move_on()

        Moves the question to the the next phase if the minimum time has
        passed. Called by the system.

        :rtype: String or Boolean
        '''
        if not self.minimum_time_passed():
            return False

         # Record timestamp of phase change
        self.last_move_on = get_timestamp()
        if self.phase == 'writing':
            self.phase = 'voting'
            db_session.commit()

        elif self.phase in {'voting', 'archive'}:
            algorithm = app.config['ALGORITHM_VERSION']
            pareto = self.calculate_pareto_front(algorithm=algorithm)
            self.phase = 'writing'
            self.generation = self.generation + 1
            db_session.commit()
            # Copy pareto to next generation
            app.logger.debug('auto_move_on copying pareto proposals to QH table %s', pareto)
            for proposal in pareto:
                self.history.append(QuestionHistory(proposal))
            db_session.commit()

        app.logger.debug('auto_move_on question now generation %s', self.generation)
        return self.phase
    
    def author_move_on(self, user_id):
        '''
        .. function:: author_move_on(user_id)

        Moves the question to the the next phase. Called by the author.

        :param user_id: Author's user ID.
        :type user_id: Integer
        :rtype: String or Boolean
        '''
        # Only the author can move a question on
        if user_id != self.user_id or not self.minimum_time_passed():
            return False

        # Record timestamp of phase change
        self.last_move_on = get_timestamp()
        if self.phase == 'writing':
            self.phase = 'voting'
            db_session.commit()

        elif self.phase in {'voting', 'archive'}:
            algorithm = app.config['ALGORITHM_VERSION']
            pareto = self.calculate_pareto_front(algorithm=algorithm)
            self.phase = 'writing'
            self.generation = self.generation + 1
            db_session.commit()
            # Copy pareto to next generation
            app.logger.debug('author_move_on copying pareto proposals to QH table %s', pareto)
            for proposal in pareto:
                self.history.append(QuestionHistory(proposal))
            # Set default threshold for voting map
            self.thresholds.append(Threshold(self))
            db_session.commit()

        app.logger.debug('author_move_on question now generation %s', self.generation)

        try:
          SEND_EMAIL_NOTIFICATIONS
        except NameError:
          app.logger.debug("SEND_EMAIL_NOTIFICATIONS not defined! Not sending email notifications!")
        else:
          if SEND_EMAIL_NOTIFICATIONS:
              # Send email notifications
              self.notify_users_moved_on()
          else:
              app.logger.debug("SEND_EMAIL_NOTIFICATIONS set to False. Not sending email notifications!")

        return self.phase

    def notify_users_moved_on(self):
        invites = self.invites.all()
        for invite in invites:
            user = User.query.get(invite.receiver_id)
            if user and user.email != '':
                emails.send_moved_on_email(user, self)
            else:
                app.logger.debug("notify_users_moved_on - user %s not found" % user.id)
    
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
        else:
            self.phase = 'writing'
            # Record timestamp of phase change
            self.last_move_on = get_timestamp()
            return True

    def move_to_voting(self):
        '''
        .. function:: move_to_writing()

        Moves the question to the writing phase if the minimum time has
        passed and and the question is currently voting or archived.

        :rtype: boolean
        '''
        if (self.phase not in ['writing', 'archived']
                or not self.minimum_time_passed()):
            return False
        else:
            self.phase = 'voting'
            # Record timestamp of phase change
            self.last_move_on = get_timestamp()
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
        # return (datetime.datetime.utcnow() - self.last_move_on)\
        #    .total_seconds() > self.minimum_time
        return get_timestamp() - self.last_move_on > self.minimum_time

    def maximum_time_passed(self):
        '''
        .. function:: maximum_time_passed()

        Returns True if the maximum time has passed for the question.

        :rtype: boolean
        '''
        # return (datetime.datetime.utcnow() - self.last_move_on)\
        #    .total_seconds() > self.maximum_time
        return get_timestamp() - self.last_move_on > self.maximum_time

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
        :type generation: int
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
        :type generation: int
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

    def voting_map(self, generation=None):
        gen = 1
        voting_map = dict()
        generation = generation or self.generation
        while gen <= generation:
            gen_proposals = self.get_proposals_list(gen)
            generation_votes = dict()
            confused_count = 0
            oppose_count = 0
            for proposal in gen_proposals:
                voters_by_type = proposal.voters_by_type(generation=gen)
                # generation_votes.append({'proposal': proposal.id, 'votes': voters_by_type})
                generation_votes[proposal.id]= {'proposal': proposal.id, 'votes': voters_by_type}
                confused_count = confused_count + len(voters_by_type['confused'])
                oppose_count = oppose_count + len(voters_by_type['oppose'])
            # voting_map.append({'generation': gen, 'votes': generation_votes})
            voting_map[gen] = {'generation': gen, 
                               'proposals': generation_votes, 
                               'confused_count': confused_count, 
                               'oppose_count': oppose_count}
            gen = gen + 1
        return voting_map

    def all_votes_by_type(self, generation=None):
        app.logger.debug("all_votes_by_type called for gen %s", generation)
        generation = generation or self.generation
        proposals = self.get_proposals_list(generation)
        all_endorsment_types = dict()
        for proposal in proposals:
            all_endorsment_types[proposal.id] = proposal.voters_by_type(generation=generation)
            app.logger.debug("proposal %s votes = %s", proposal.id, all_endorsment_types[proposal.id])
        return all_endorsment_types

    def get_proposals_list_by_id(self, generation=None):
        '''
        .. function:: get_proposals()

        Returns a set of proposals for the current generation of
        the question.

        :param generation: question generation.
        :type generation: int
        :rtype: set
        '''
        generation = generation or self.generation
        proposals_list = self.get_proposals_list(generation)
        proposals_by_id = dict()
        for prop in proposals_list:
            proposals_by_id[prop.id] = prop
        return proposals_by_id
    
    def get_proposals_list(self, generation=None):
        '''
        .. function:: get_proposals()

        Returns a set of proposals for the current generation of
        the question.

        :param generation: question generation.
        :type generation: int
        :rtype: set
        '''
        generation = generation or self.generation

        proposals = db_session.query(Proposal).join(QuestionHistory).\
            filter(QuestionHistory.question_id == self.id).\
            filter(QuestionHistory.generation == generation).\
            order_by(Proposal.id).\
            all()
        return proposals

    def get_proposals(self, generation=None):
        '''
        .. function:: get_proposals()

        Returns a set of proposals for the current generation of
        the question.

        :param generation: question generation.
        :type generation: int
        :rtype: set
        '''
        generation = generation or self.generation

        proposals = db_session.query(Proposal).join(QuestionHistory).\
            filter(QuestionHistory.question_id == self.id).\
            filter(QuestionHistory.generation == generation).\
            order_by(Proposal.id).\
            all()
        return set(proposals)

    def has_endorsememnts(self, generation=None):
        generation = generation or self.generation
        app.logger.debug("has_endorsememnts: Generation: %s ", generation)
        ids = list(self.get_proposal_ids(generation))
        app.logger.debug('has_endorsememnts: ids ==> %s', ids)
        if len(ids) == 0:
            return 0
        else:
            return db_session.query(Endorsement)\
                .filter(Endorsement.proposal_id.in_(x for x in ids))\
                .filter(Endorsement.generation == generation)\
                .count()

    def get_proposal_ids_new(self, generation=None):
        generation = generation or self.generation
        ids = self.history\
            .with_entities(QuestionHistory.question_id)\
            .filter(QuestionHistory.generation == generation)\
            .filter(QuestionHistory.question_id == self.id)\
            .all()
        return set(ids)

    def get_proposal_ids(self, generation=None):
        '''
        .. function:: get_proposal_ids([generation=None])

        Returns a set of proposal IDs for the current generation of
        the question.

        :param generation: question generation.
        :type generation: int
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
        :type generation: int
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
        .. function:: which_element_dominates_which(element1, element2)

        Takes 2 SETS and calulates which element if any
        domiantes the other.
        Returns either the dominating set, or an db.Integer value of:

            - 0 if the sets of endorsers are different
            - -1 if the sets of endorsers are the same

        :param element1: element 1
        :type element1: set of int
        :param element2: element 2
        :type element2: set of int
        :rtype: interger or set of int
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
        :type generation: int
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

    # NEW VERSION !!! MAP
    def calculate_endorser_relations_2(self, proposals, generation=None):
        '''
        .. function:: calculate_endorser_relations([generation=None])

        Calculates the complete map of dominations. For each endorser
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        generation = generation or self.generation

        endorser_relations = dict()
        endorsements = dict()
        all_endorsers = self.get_endorsers(generation)
        for e in all_endorsers:
            endorsements[e.id] = e.get_endorsed_proposal_ids_2(self, proposals, generation)

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

    def calculate_proposal_relations_NEW(self, generation=None, proposals=None, algorithm=None):
        '''
        .. function:: calculate_proposal_relations([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        algorithm = algorithm or app.config['ALGORITHM_VERSION']

        if algorithm == 2:
            # app.logger.debug("************** USING ALGORITHM 2 ************")
            return self.calculate_proposal_relations_qualified(generation=generation,
                                                               proposals=proposals,
                                                               algorithm=algorithm)
        else:
            # app.logger.debug("************** USING ALGORITHM 1 ************")
            return self.calculate_proposal_relations_original(generation=generation,
                                                             proposals=proposals)

    def calculate_proposal_relations_original_v_whatever(self, generation=None, proposals=None, algorithm=None):
        '''
        .. function:: calculate_proposal_relations([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        generation = generation or self.generation

        proposal_relations = dict()
        props = dict()

        # all_proposals = self.get_proposals(generation)
        all_proposals = proposals or self.get_proposals(generation)

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
    
    def calculate_proposal_relations(self, generation=None, proposals=None, algorithm=None):
        '''
        .. function:: calculate_proposal_relations([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        generation = generation or self.generation

        proposal_relations = dict()
        props = dict()

        # all_proposals = self.get_proposals(generation)
        all_proposals = proposals or self.get_proposals(generation)

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


    def calculate_proposal_relation_ids(self, generation=None, proposals=None, algorithm=None):
        '''
        .. function:: calculate_proposal_relations([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        algorithm = algorithm or app.config['ALGORITHM_VERSION']
                
        generation = generation or self.generation
        
        app.logger.debug("calculate_proposal_relation_ids called with gen %s", generation)

        filenamehash = make_new_map_filename_hashed(self,
                                                    generation,
                                                    algorithm)

        app.logger.debug("calculate_proposal_relation_ids: filenamehash = %s", filenamehash)

        filepath = app.config['WORK_FILE_DIRECTORY'] + '/' + 'prop_rel_ids_' + filenamehash + '.pkl'

        app.logger.debug("calculate_proposal_relation_ids: check for cache file %s", filepath)
        
        if app.config['CACHE_COMPLEX_DOM']:
            if os.path.isfile(filepath):
                app.logger.debug('calculate_proposal_relation_ids: RETURNING CACHED DATA')
                with open(filepath, 'rb') as input:
                    return pickle.load(input)
            else:
                app.logger.debug("calculate_proposal_relation_ids: Cache file %s not found", filepath)

        # return 
        
        if algorithm == 2:
            # app.logger.debug("************** USING ALGORITHM 2 ************")
            app.logger.debug('calculate_proposal_relation_ids: NON CACHED DATA')
            proposal_relation_ids = self.calculate_proposal_relation_ids_qualified(generation=generation,
                                                                  proposals=proposals)
        else:
            # app.logger.debug("************** USING ALGORITHM 1 ************")
            app.logger.debug('calculate_proposal_relation_ids: NON CACHED DATA')
            proposal_relation_ids = self.calculate_proposal_relation_ids_original(generation=generation,
                                                                 proposals=proposals)
        if app.config['CACHE_COMPLEX_DOM']:
            app.logger.debug("calculate_proposal_relation_ids: saving cache to file %s", filepath)
            save_object(proposal_relation_ids, r'' + filepath)
        
        return proposal_relation_ids

    def calculate_proposal_relation_ids_original(self, generation=None, proposals=None):
        '''
        .. function:: calculate_proposal_relations([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        generation = generation or self.generation

        proposal_relations = dict()
        endorser_ids = dict()

        # all_proposals = self.get_proposals(generation)
        all_proposals = proposals or self.get_proposals(generation)

        for p in all_proposals:
            endorser_ids[p.id] = p.set_of_endorser_ids(generation)

        for proposal1 in all_proposals:
            dominating = set()
            dominated = set()
            proposal_relations[proposal1.id] = dict()

            for proposal2 in all_proposals:
                if (proposal1 == proposal2):
                    continue
                who_dominates = Proposal.\
                    who_dominates_who(endorser_ids[proposal1.id],
                                      endorser_ids[proposal2.id])

                '''
                app.logger.debug("Comparing endorser_ids %s %s and %s %s\n",
                                 proposal1.id, endorser_ids[proposal1.id],
                                 proposal2.id, endorser_ids[proposal2.id])
                app.logger.debug("   ===> WDW Result = %s\n",
                                 who_dominates)
                '''

                if (who_dominates == endorser_ids[proposal1.id]):
                    dominating.add(proposal2.id)
                elif (who_dominates == endorser_ids[proposal2.id]):
                    dominated.add(proposal2.id)

            proposal_relations[proposal1.id]['dominating'] = dominating
            proposal_relations[proposal1.id]['dominated'] = dominated

        return proposal_relations

    def calculate_proposal_relation_ids_qualified_v2(self, generation=None, proposals=None):
        '''
        .. function:: calculate_proposal_relations([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        generation = generation or self.generation

        proposal_relations = dict()
        endorser_ids = dict()

        # all_proposals = self.get_proposals(generation)
        all_proposals = proposals or self.get_proposals(generation)
        
        # Get all votes sorted into sets by type for this genration
        votes = self.all_votes_by_type(generation=generation)
        app.logger.debug("votes ==> %s", votes)

        for p in all_proposals:
            endorser_ids[p.id] = p.set_of_endorser_ids(generation)

        for proposal1 in all_proposals:
            dominating = set()
            dominated = set()
            proposal_relations[proposal1.id] = dict()

            for proposal2 in all_proposals:
                if (proposal1 == proposal2):
                    continue

                qualified_voters = Proposal.\
                    intersection_of_qualfied_endorser_ids(proposal1,
                                                          proposal2,
                                                          generation)
                # app.logger.debug("Complex Domination: qualified_voters ==> %s", qualified_voters)

                who_dominates = Proposal.\
                    who_dominates_who_qualified(endorser_ids[proposal1.id], # newgraph
                                                endorser_ids[proposal2.id],
                                                qualified_voters)

                '''
                app.logger.debug("Comparing endorser_ids %s %s and %s %s\n",
                                 proposal1.id, endorser_ids[proposal1.id],
                                 proposal2.id, endorser_ids[proposal2.id]) final
                app.logger.debug("   ===> WDW Result = %s\n",
                                 who_dominates)
                '''

                partial_understanding = len(votes[proposal1.id]['confused']) > 0 or len(votes[proposal2.id]['confused']) > 0

                if (who_dominates == endorser_ids[proposal1.id]): # newgraph
                    # dominating
                    if partial_understanding:
                        app.logger.debug("Testing Partials A = PID %s and B = PID %s", proposal1.id, proposal2.id)
                        app.logger.debug("Test1: A? %s < B- %s", votes[proposal1.id]['confused'], votes[proposal2.id]['oppose'])
                        app.logger.debug("Test2: B? %s < A+ %s", votes[proposal2.id]['confused'], votes[proposal1.id]['endorse'])

                        if self.converts_to_full_domination(votes, proposal1, proposal2):
                            app.logger.debug("Partial converts...")
                            # domination_map[proposal1.id][proposal2.id] = 5
                            dominating.add(proposal2.id)
                        else:
                            app.logger.debug("Partial does not convert...")
                    else:
                        domination_map[proposal1.id][proposal2.id] = 1
                elif (who_dominates == endorser_ids[proposal2.id]):
                    # dominated
                    if partial_understanding and self.converts_to_full_domination(votes, proposal2, proposal1):
                            dominated.add(proposal2.id)
                    else:
                        dominated.add(proposal2.id)

            proposal_relations[proposal1.id]['dominating'] = dominating
            proposal_relations[proposal1.id]['dominated'] = dominated
            # Add whether or not the proposal is fully understood
            proposal_relations[proposal1.id]['understood'] = proposal1.is_completely_understood(generation=generation)

        return proposal_relations
    
    def calculate_proposal_relation_ids_qualified(self, generation=None, proposals=None):
        '''
        .. function:: calculate_proposal_relations([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        generation = generation or self.generation

        proposal_relations = dict()
        endorser_ids = dict()

        # all_proposals = self.get_proposals(generation)
        all_proposals = proposals or self.get_proposals(generation)

        for p in all_proposals:
            endorser_ids[p.id] = p.set_of_endorser_ids(generation)

        for proposal1 in all_proposals:
            dominating = set()
            dominated = set()
            proposal_relations[proposal1.id] = dict()

            for proposal2 in all_proposals:
                if (proposal1 == proposal2):
                    continue

                qualified_voters = Proposal.\
                    intersection_of_qualfied_endorser_ids(proposal1,
                                                          proposal2,
                                                          generation)
                # app.logger.debug("Complex Domination: qualified_voters ==> %s", qualified_voters)

                who_dominates = Proposal.\
                    who_dominates_who_qualified(endorser_ids[proposal1.id], # newgraph
                                                endorser_ids[proposal2.id],
                                                qualified_voters)

                '''
                app.logger.debug("Comparing endorser_ids %s %s and %s %s\n",
                                 proposal1.id, endorser_ids[proposal1.id],
                                 proposal2.id, endorser_ids[proposal2.id])
                app.logger.debug("   ===> WDW Result = %s\n",
                                 who_dominates)
                '''

                if (who_dominates == endorser_ids[proposal1.id]):
                    dominating.add(proposal2.id)
                elif (who_dominates == endorser_ids[proposal2.id]):
                    dominated.add(proposal2.id)

            proposal_relations[proposal1.id]['dominating'] = dominating
            proposal_relations[proposal1.id]['dominated'] = dominated
            proposal_relations[proposal1.id]['pareto'] = len(dominated) == 0
            # Add whether or not the proposal is fully understood
            proposal_relations[proposal1.id]['understood'] = proposal1.is_completely_understood(generation=generation)

        return proposal_relations
    
    def calculate_proposal_relations_original_v1(self, generation=None, proposals=None): 
        '''
        .. function:: calculate_proposal_relations_original([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        app.logger.debug("calculate_proposal_relations_original called...")

        generation = generation or self.generation
        proposal_relations = dict()
        props = dict()

        all_proposals = proposals or self.get_proposals(generation)

        for p in all_proposals:
            props[p.id] = p.set_of_endorser_ids(generation)

        for proposal1 in all_proposals:
            dominating = set()
            dominated = set()
            proposal_relations[proposal1.id] = dict()

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

            proposal_relations[proposal1.id]['dominating'] = dominating
            proposal_relations[proposal1.id]['dominated'] = dominated

        app.logger.debug("Simple Domination: Relation Map ==> %s", proposal_relations)
        return proposal_relations
    
    def calculate_proposal_relations_qualified_v1(self,
                                               generation=None,
                                               proposals=None,
                                               algorithm=None):
        '''
        .. function:: calculate_proposal_relations_qualified([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        app.logger.debug("calculate_proposal_relations_qualified called...")

        generation = generation or self.generation
        proposal_relations = dict()
        props = dict()

        all_proposals = proposals or self.get_proposals(generation)

        for p in all_proposals:
            props[p.id] = p.set_of_endorser_ids(generation)

        for proposal1 in all_proposals:
            dominating = set()
            dominated = set()
            proposal_relations[proposal1] = dict()

            for proposal2 in all_proposals:
                if (proposal1 == proposal2):
                    continue

                qualified_voters = Proposal.\
                    intersection_of_qualfied_endorser_ids(proposal1,
                                                          proposal2,
                                                          generation)
                # app.logger.debug("Complex Domination: qualified_voters ==> %s", qualified_voters)

                who_dominates = Proposal.\
                    who_dominates_who_qualified(props[proposal1.id],
                                                props[proposal2.id],
                                                qualified_voters)

                if (who_dominates == props[proposal1.id]):
                    dominating.add(proposal2)
                elif (who_dominates == props[proposal2.id]):
                    dominated.add(proposal2)

            proposal_relations[proposal1.id]['dominating'] = dominating
            proposal_relations[proposal1.id]['dominated'] = dominated
            # app.logger.debug("Complex Domination: Relation Map ==> %s", proposal_relations)

        return proposal_relations

    
    def calculate_levels_map_off(self, generation=None, proposals=None, algorithm=None): # test_complex
        '''
        .. function:: calculate_levels_map([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        algorithm = algorithm or app.config['ALGORITHM_VERSION']

        if algorithm == 2:
            # app.logger.debug("************** USING ALGORITHM 2 ************")
            return self.calculate_levels_map_qualified(generation=generation,
                                                       proposals=proposals,
                                                       algorithm=algorithm)
        else:
            # app.logger.debug("************** USING ALGORITHM 1 ************")
            return self.calculate_levels_map_original(generation=generation,
                                                      proposals=proposals,
                                                      algorithm=algorithm)

    def calculate_levels_map(self, generation=None, proposals=None, algorithm=None):
        '''
        .. function:: calculate_levels_map_original([generation=None, proposals=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        app.logger.debug("FUNCTION calculate_levels_map_original VERSION = %s", 2)
        
        generation = generation or self.generation

        domination_map = self.calculate_domination_map(generation=generation, proposals=proposals, algorithm=algorithm)
        app.logger.debug("domination_map = %s", domination_map)
        # return "CALCULATED DOMINATION MAP !!!!!"
        
        levels_map = dict()
        relations = self.calculate_proposal_relation_ids(generation=generation, algorithm=algorithm)
        app.logger.debug("relations = %s", relations)
        # return "CALCULATED PROPOSAL RELATIONS !!!!!"
        
        num_proposals = len(relations)
        # app.logger.debug("num_proposals = %s", num_proposals)
        
        # set of all proposal ids
        all_pids = set(relations.keys())
        app.logger.debug("all_pids = %s", all_pids)
        
        top_done = set()
        bottom_done = set()
        top_levels = dict()
        bottom_levels = dict()
        
        # set top and bottom levels
        top_levels[0] = set()
        bottom_levels[0] = set()
        pareto = set()
        
        for (proposal_id, dominations) in domination_map.iteritems():
            # Initialize map
            levels_map[proposal_id] = {'dominates': -1, 'dominated': -1, 'pf_dominated': '&hellip;'}

            # Test if proposal is undominated
            if 2 not in dominations.values():
                pareto.add(proposal_id)
                levels_map[proposal_id]['dominated'] = 0
                levels_map[proposal_id]['pf_dominated'] = 0
                top_done.add(proposal_id)
                top_levels[0].add(proposal_id)

            # Test if proposal dominates nothing
            if 1 not in dominations.values():
                levels_map[proposal_id]['dominates'] = 0
                bottom_done.add(proposal_id)
                bottom_levels[0].add(proposal_id)

        
        for (proposal_id, rel) in relations.iteritems():
            if len(rel['dominated'] & top_levels[0]) > 0:
                levels_map[proposal_id]['pf_dominated'] = 1
        
        '''
        today
        
        relations
        {1: {'dominated': set(), 'dominating': {2}},
         2: {'dominated': {1}, 'dominating': set()},
         3: {'dominated': set(), 'dominating': set()},
         4: {'dominated': set(), 'dominating': set()}}
         
         {1: {'dominated': set([]), 'dominating': set([2])}, 
         2: {'dominated': set([1]), 'dominating': set([])}, 
         3: {'dominated': set([]), 'dominating': set([])}, 
         4: {'dominated': set([]), 'dominating': set([])}}
        
        domination_map
        {1: {1: -1, 2: 1, 3: 0, 4: 0},
         2: {1: 2, 2: -1, 3: 0, 4: 0},
         3: {1: 0, 2: 0, 3: -1, 4: 0},
         4: {1: 0, 2: 0, 3: 0, 4: -1}}
        
        paretomap
        {1: {'dominated': 0, 'dominates': -1},
         2: {'dominated': -1, 'dominates': 0},
         3: {'dominated': 0, 'dominates': 0},
         4: {'dominated': 0, 'dominates': 0}}
        '''
        
        
        # Finish levels below pareto
        app.logger.debug("Finish levels below pareto")
        app.logger.debug("num_proposals = %s", num_proposals)
        app.logger.debug("top_done = %s", top_done)
        level = 1
        # Initialize higher_levels set with pareto - the top level
        higher_levels = top_done.copy()
        app.logger.debug("higher_levels initialized to top_done = %s", higher_levels)
        
        while top_done != all_pids:
            app.logger.debug("**************OUTER: Level %s**************", level)
            app.logger.debug("**************OUTER: higher_levels = %s**************", higher_levels)
            top_levels[level] = set()
            for proposal_id in all_pids:
                app.logger.debug("**************PID %s**************", proposal_id)
                if proposal_id in top_done:
                    app.logger.debug("Proposal %s already in competed set %s - SKIP", proposal_id, top_done)
                    continue
                doms = relations[proposal_id]['dominated']
                app.logger.debug("Relations = %s", doms)
                                
                app.logger.debug("Test if proposals dominations %s is a subset of higher levels %s",
                                     doms, higher_levels)

                if doms <= higher_levels:
                    app.logger.debug("IS SUBSET: proposal_id %s dominated by levels %s and up - adding to level %s",
                                     proposal_id, level-1, level)
                    levels_map[proposal_id]['dominated'] = level
                    top_done.add(proposal_id)
                    top_levels[level].add(proposal_id)
                else:
                    app.logger.debug("IS NOT SUBSET")
            
            app.logger.debug("Adding current level %s pids to higher_levels %s", top_levels[level], higher_levels)
            higher_levels = higher_levels | top_levels[level]
            app.logger.debug("higher_levels now %s", higher_levels)
            level = level + 1
            app.logger.debug("level now %s", level)
            '''
            if level > 3:
                app.logger.debug("at level %s - BREAKING!!!", level)
                break
            '''
        
        app.logger.debug("Completed: top_done = %s", top_done)
        app.logger.debug("Completed: top_levels = %s", top_levels)
        
        # return levels_map
        
        level = 1
        # Initialize lower_levels set with pareto - the top level
        lower_levels = bottom_done.copy()
        app.logger.debug("lower_levels initialized to bottom_done = %s", lower_levels)
        
        while bottom_done != all_pids:
            app.logger.debug("**************OUTER: Level %s**************", level)
            app.logger.debug("**************OUTER: lower_levels = %s**************", lower_levels)
            bottom_levels[level] = set()
            for proposal_id in all_pids:
                app.logger.debug("**************PID %s**************", proposal_id)
                if proposal_id in bottom_done:
                    app.logger.debug("Proposal %s already in competed set %s - SKIP", proposal_id, bottom_done)
                    continue
                doms = relations[proposal_id]['dominating']
                app.logger.debug("Relations = %s", doms)
                                
                app.logger.debug("Test if proposals dominations %s is a subset of lower levels %s",
                                     doms, lower_levels)

                if doms <= lower_levels:
                    app.logger.debug("IS SUBSET: proposal_id %s dominating levels %s and up - adding to level %s",
                                     proposal_id, level-1, level)
                    levels_map[proposal_id]['dominates'] = level
                    bottom_done.add(proposal_id)
                    bottom_levels[level].add(proposal_id)
                else:
                    app.logger.debug("IS NOT SUBSET")
            
            app.logger.debug("Adding current level %s pids to lower_levels %s", bottom_levels[level], lower_levels)
            lower_levels = lower_levels | bottom_levels[level]
            app.logger.debug("lower_levels now %s", lower_levels)
            level = level + 1
            app.logger.debug("level now %s", level)
            '''
            if level > 3:
                app.logger.debug("at level %s - BREAKING!!!", level)
                break
            '''

        return levels_map
    
    def calculate_levels_map_qualified(self, generation=None, proposals=None, algorithm=None):
        '''
        .. function:: calculate_levels_map_original([generation=None, proposals=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        app.logger.debug("FUNCTION calculate_levels_map_original VERSION = %s", 2)
        
        generation = generation or self.generation

        domination_map = self.calculate_domination_map_qualified(generation=generation, proposals=proposals)
        app.logger.debug("domination_map = %s", domination_map)
        
        levels_map = dict()
        relations = self.calculate_proposal_relation_ids(generation=generation, algorithm=algorithm)
        
        app.logger.debug("relations = %s", relations)
        
        num_proposals = len(relations)
        # app.logger.debug("num_proposals = %s", num_proposals)
        
        # set of all proposal ids
        all_pids = set(relations.keys())
        app.logger.debug("all_pids = %s", all_pids)
        
        top_done = set()
        bottom_done = set()
        top_levels = dict()
        bottom_levels = dict()
        
        # set top and bottom levels
        top_levels[0] = set()
        bottom_levels[0] = set()
        
        for (proposal_id, dominations) in domination_map.iteritems():
            # Initialize map
            levels_map[proposal_id] = {'dominates': -1, 'dominated': -1}

            # Test if proposal is undominated
            if 2 not in dominations.values():
                levels_map[proposal_id]['dominated'] = 0
                top_done.add(proposal_id)
                top_levels[0].add(proposal_id)

            # Test if proposal dominates nothing
            if 1 not in dominations.values():
                levels_map[proposal_id]['dominates'] = 0
                bottom_done.add(proposal_id)
                bottom_levels[0].add(proposal_id)

        '''
        today
        
        relations
        {1: {'dominated': set(), 'dominating': {2}},
         2: {'dominated': {1}, 'dominating': set()},
         3: {'dominated': set(), 'dominating': set()},
         4: {'dominated': set(), 'dominating': set()}}
         
         {1: {'dominated': set([]), 'dominating': set([2])}, 
         2: {'dominated': set([1]), 'dominating': set([])}, 
         3: {'dominated': set([]), 'dominating': set([])}, 
         4: {'dominated': set([]), 'dominating': set([])}}
        
        domination_map
        {1: {1: -1, 2: 1, 3: 0, 4: 0},
         2: {1: 2, 2: -1, 3: 0, 4: 0},
         3: {1: 0, 2: 0, 3: -1, 4: 0},
         4: {1: 0, 2: 0, 3: 0, 4: -1}}
        
        paretomap
        {1: {'dominated': 0, 'dominates': -1},
         2: {'dominated': -1, 'dominates': 0},
         3: {'dominated': 0, 'dominates': 0},
         4: {'dominated': 0, 'dominates': 0}}
        '''
        
        
        # Finish levels below pareto
        app.logger.debug("Finish levels below pareto")
        app.logger.debug("num_proposals = %s", num_proposals)
        app.logger.debug("top_done = %s", top_done)
        level = 1
        # Initialize higher_levels set with pareto - the top level
        higher_levels = top_done.copy()
        app.logger.debug("higher_levels initialized to top_done = %s", higher_levels)
        
        while top_done != all_pids:
            app.logger.debug("**************OUTER: Level %s**************", level)
            app.logger.debug("**************OUTER: higher_levels = %s**************", higher_levels)
            top_levels[level] = set()
            for proposal_id in all_pids:
                app.logger.debug("**************PID %s**************", proposal_id)
                if proposal_id in top_done:
                    app.logger.debug("Proposal %s already in competed set %s - SKIP", proposal_id, top_done)
                    continue
                doms = relations[proposal_id]['dominated']
                app.logger.debug("Relations = %s", doms)
                                
                # if len(doms - top_done) == 0:
                app.logger.debug("Test if proposals dominations %s is a subset of higher levels %s",
                                     doms, higher_levels)

                if doms <= higher_levels:
                    app.logger.debug("IS SUBSET: proposal_id %s dominated by levels %s and up - adding to level %s",
                                     proposal_id, level-1, level)
                    levels_map[proposal_id]['dominated'] = level
                    top_done.add(proposal_id)
                    top_levels[level].add(proposal_id)
                else:
                    app.logger.debug("IS NOT SUBSET")
            
            app.logger.debug("Adding current level %s pids to higher_levels %s", top_levels[level], higher_levels)
            higher_levels = higher_levels | top_levels[level]
            app.logger.debug("higher_levels now %s", higher_levels)
            level = level + 1
            app.logger.debug("level now %s", level)
            '''
            if level > 3:
                app.logger.debug("at level %s - BREAKING!!!", level)
                break
            '''
        
        app.logger.debug("Completed: top_done = %s", top_done)
        app.logger.debug("Completed: top_levels = %s", top_levels)
        
        # return levels_map
        
        level = 1
        # Initialize lower_levels set with pareto - the top level
        lower_levels = bottom_done.copy()
        app.logger.debug("lower_levels initialized to bottom_done = %s", lower_levels)
        
        while bottom_done != all_pids:
            app.logger.debug("**************OUTER: Level %s**************", level)
            app.logger.debug("**************OUTER: lower_levels = %s**************", lower_levels)
            bottom_levels[level] = set()
            for proposal_id in all_pids:
                app.logger.debug("**************PID %s**************", proposal_id)
                if proposal_id in bottom_done:
                    app.logger.debug("Proposal %s already in competed set %s - SKIP", proposal_id, bottom_done)
                    continue
                doms = relations[proposal_id]['dominating']
                app.logger.debug("Relations = %s", doms)
                                
                # if len(doms - bottom_done) == 0:
                app.logger.debug("Test if proposals dominations %s is a subset of lower levels %s",
                                     doms, lower_levels)

                if doms <= lower_levels:
                    app.logger.debug("IS SUBSET: proposal_id %s dominating levels %s and up - adding to level %s",
                                     proposal_id, level-1, level)
                    levels_map[proposal_id]['dominates'] = level
                    bottom_done.add(proposal_id)
                    bottom_levels[level].add(proposal_id)
                else:
                    app.logger.debug("IS NOT SUBSET")
            
            app.logger.debug("Adding current level %s pids to lower_levels %s", bottom_levels[level], lower_levels)
            lower_levels = lower_levels | bottom_levels[level]
            app.logger.debug("lower_levels now %s", lower_levels)
            level = level + 1
            app.logger.debug("level now %s", level)
            

            if level > 50:
                app.logger.debug("at level %s - BREAKING!!!", level)
                break

        return levels_map


    def calculate_levels_map_qualified_v1(self, generation=None, proposals=None, algorithm=None):
        '''
        .. function:: calculate_levels_map_original([generation=None, proposals=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        generation = generation or self.generation

        domination_map = self.calculate_domination_map_qualified(generation=generation, proposals=proposals)
        app.logger.debug("domination_map = %s", domination_map)
        
        levels_map = dict()
        relations = self.calculate_proposal_relation_ids(generation=generation, algorithm=algorithm)
        app.logger.debug("relations = %s", relations)
        
        num_proposals = len(relations)
        app.logger.debug("num_proposals = %s", num_proposals)
        
        # set of all proposal ids
        all_pids = set(relations.keys())
        top_done = set()
        bottom_done = set()
        top_levels = dict()
        bottom_levels = dict()
        
        # set top and bottom levels
        top_levels[0] = set()
        bottom_levels[0] = set()
        
        for (proposal_id, dominations) in domination_map.iteritems():
            # Initialize map
            levels_map[proposal_id] = {'dominates': -1, 'dominated': -1}

            # Test if proposal is undominated
            if 2 not in dominations.values():
                levels_map[proposal_id]['dominated'] = 0
                top_done.add(proposal_id)
                top_levels[0].add(proposal_id)

            # Test if proposal dominates nothing
            if 1 not in dominations.values():
                levels_map[proposal_id]['dominates'] = 0
                bottom_done.add(proposal_id)
                bottom_levels[0].add(proposal_id)

        '''
        today
        
        relations
        {1: {'dominated': set(), 'dominating': {2}},
         2: {'dominated': {1}, 'dominating': set()},
         3: {'dominated': set(), 'dominating': set()},
         4: {'dominated': set(), 'dominating': set()}}
         
         {1: {'dominated': set([]), 'dominating': set([2])}, 
         2: {'dominated': set([1]), 'dominating': set([])}, 
         3: {'dominated': set([]), 'dominating': set([])}, 
         4: {'dominated': set([]), 'dominating': set([])}}
        
        domination_map
        {1: {1: -1, 2: 1, 3: 0, 4: 0},
         2: {1: 2, 2: -1, 3: 0, 4: 0},
         3: {1: 0, 2: 0, 3: -1, 4: 0},
         4: {1: 0, 2: 0, 3: 0, 4: -1}}
        
        paretomap
        {1: {'dominated': 0, 'dominates': -1},
         2: {'dominated': -1, 'dominates': 0},
         3: {'dominated': 0, 'dominates': 0},
         4: {'dominated': 0, 'dominates': 0}}
        '''
                
        # Finish levels below pareto
        app.logger.debug("Finish levels below pareto")
        app.logger.debug("num_proposals = %s", num_proposals)
        app.logger.debug("top_done = %s", top_done)
        level = 1
        for proposal_id in all_pids:
            if proposal_id in top_done:
                continue
            top_levels[level] = set()
            app.logger.debug("top_done = %s", top_done)
            doms = relations[proposal_id]['dominated']
            app.logger.debug("doms = %s", doms)
            app.logger.debug("doms - top_done = %s", doms - top_done)
            app.logger.debug("len(doms - top_done) == %s", len(doms - top_done))
            if len(doms - top_done) == 0:
                app.logger.debug("proposal_id %s dominated by levels %s and up - adding to level %s", proposal_id, level-1, level)
                levels_map[proposal_id]['dominated'] = level
                top_done.add(proposal_id)
                top_levels[level].add(proposal_id)
                
            level = level + 1
            '''
            if level > 1:
                app.logger.debug("at level %s", level)
                break
            '''
        # return levels_map
        
        level = 1
        for proposal_id in all_pids:
            if proposal_id in bottom_done:
                continue
            bottom_levels[level] = set()
            app.logger.debug("bottom_done = %s", bottom_done)
            doms = relations[proposal_id]['dominating']
            app.logger.debug("doms = %s", doms)
            app.logger.debug("doms - bottom_done = %s", doms - bottom_done)
            app.logger.debug("len(doms - bottom_done) == %s", len(doms - bottom_done))
            if len(doms - bottom_done) == 0:
                app.logger.debug("proposal_id %s dominating levels %s and up - adding to level %s", proposal_id, level-1, level)
                levels_map[proposal_id]['dominates'] = level
                bottom_done.add(proposal_id)
                bottom_levels[level].add(proposal_id)
                
            level = level + 1
            '''
            if level > 1:
                app.logger.debug("at level %s", level)
                break
            '''
        return levels_map

    def calculate_domination_map(self, generation=None, proposals=None, algorithm=None): # 
        '''
        .. function:: calculate_domination_map([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        algorithm = algorithm or app.config['ALGORITHM_VERSION']

        generation = generation or self.generation

        
        filenamehash = make_new_map_filename_hashed(self,
                                                    generation,
                                                    algorithm)
        
        app.logger.debug("calculate_domination_map: filenamehash = %s", filenamehash)

        filepath = app.config['WORK_FILE_DIRECTORY'] + '/' + 'dom_map_' + filenamehash + '.pkl'
                
        app.logger.debug("calculate_domination_map: check for cache file %s", filepath)

        if app.config['CACHE_COMPLEX_DOM']:
            if os.path.isfile(filepath):
                app.logger.debug('calculate_domination_map: RETURNING CACHED DATA')
                with open(filepath, 'rb') as input:
                    return pickle.load(input)
            else:
                app.logger.debug("Cache file %s not found", filepath)

        # return
        
        if algorithm == 2:
            # app.logger.debug("************** USING ALGORITHM 2 ************")
            app.logger.debug('calculate_domination_map_qualified: NON CACHED DATA')
            dom_map = self.calculate_domination_map_qualified(generation=generation,
                                                               proposals=proposals)
        else:
            # app.logger.debug("************** USING ALGORITHM 1 ************")
            app.logger.debug('calculate_domination_map_original: NON CACHED DATA')
            dom_map = self.calculate_domination_map_original(generation=generation,
                                                             proposals=proposals)
        if app.config['CACHE_COMPLEX_DOM']:
            save_object(dom_map, r'' + filepath)

        return dom_map

    def converts_to_full_domination(self, votes, A, B):
        app.logger.debug("Testing Partials A = PID %s and B = PID %s", A.id, B.id)
        test1 = set(votes[A.id]['confused']) < set(votes[B.id]['oppose'])
        app.logger.debug("Test1: A? %s < B- %s ==> %s", votes[A.id]['confused'], votes[B.id]['oppose'], test1)
        
        test2 = set(votes[B.id]['confused']) < set(votes[A.id]['endorse'])
        app.logger.debug("Test2: B? %s < A+ %s ==> %s", votes[B.id]['confused'], votes[A.id]['endorse'], test2)
        
        votes[B.id]['confused'] < votes[A.id]['endorse']
        return set(votes[A.id]['confused']) < set(votes[B.id]['oppose'])\
            and set(votes[B.id]['confused']) < set(votes[A.id]['endorse'])
    
    def set_domination_table_entry():
        pass
    
    def calculate_domination_map_qualified(self, generation=None, proposals=None):  
        '''
        .. function:: calculate_domination_map_qualified([generation=None, proposals=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation. today 2
        :type generation: int
        :rtype: dict
        '''
        app.logger.debug("CALCULATE_DOMINATION_MAP_QUALIFIED CALLED...")

        reverse_values = {-2: -2, -1: -1, 0: 0, 1: 2, 2: 1, 3: 4, 4: 3, 5: 6, 6: 5}

        generation = generation or self.generation
        app.logger.debug("calculate_domination_map_qualified: called with generation %s", generation)
        domination_map = dict()
        endorser_ids = dict()

        all_proposals = proposals or self.get_proposals_list(generation)
        
        # Get all votes sorted into sets by type for this genration
        votes = self.all_votes_by_type(generation=generation)
        app.logger.debug("votes ==> %s", votes)

        # app.logger.debug("Processing %s proposals", len(all_proposals))

        for p in all_proposals:
            endorser_ids[p.id] = p.set_of_endorser_ids(generation)

        outer_counter = 0

        for proposal1 in all_proposals:
            if domination_map.get(proposal1.id, None) is None:
                domination_map[proposal1.id] = dict()

            outer_counter = outer_counter + 1
            # app.logger.debug("********************* OUTER PROPOSAL COUNTER = %s ********************* ", outer_counter)

            inner_counter = 0

            for proposal2 in all_proposals:
                inner_counter = inner_counter + 1
                # Test for same proposal
                if (proposal1 == proposal2):
                    domination_map[proposal1.id][proposal2.id] = -1
                    continue
                
                # Check if the two proposals are equivalent
                elif votes[proposal1.id]['oppose'] == votes[proposal2.id]['oppose'] and\
                        votes[proposal1.id]['endorse'] == votes[proposal2.id]['endorse'] and\
                        votes[proposal1.id]['confused'] == votes[proposal2.id]['confused']:
                    domination_map[proposal1.id][proposal2.id] = -1
                    if domination_map.get(proposal2.id, None) is None:
                        domination_map[proposal2.id] = dict()
                    domination_map[proposal2.id][proposal1.id] = -1
                    continue
                    
                if not domination_map[proposal1.id].get(proposal2.id, None) is None:
                    '''
                    app.logger.debug("**** Domination_map entry [%s][%s] already set: skip",
                        proposal1.id,
                        proposal2.id)
                    '''
                    continue

                qualified_voters = Proposal.\
                    intersection_of_qualfied_endorser_ids(proposal1,
                                                          proposal2,
                                                          generation)

                # app.logger.debug("Proposal %s votes == %s", proposal1.id, endorser_ids[proposal1.id])
                # app.logger.debug("Proposal %s votes == %s", proposal2.id, endorser_ids[proposal2.id])
                '''
                app.logger.debug("Complex Domination: qualified_voters for %s and %s ==> %s",
                    proposal1.id,
                    proposal2.id,
                    qualified_voters)
                '''

                who_dominates = Proposal.\
                    who_dominates_who_qualified(endorser_ids[proposal1.id],
                                                endorser_ids[proposal2.id],
                                                qualified_voters)
                app.logger.debug("who dominates returned ==> %s", who_dominates)

                '''
                ^ = intersection
                < = subset
                \ = set minus. (A\B= elements that are in A but not in B)
                0 = empty set.
                => = implies

                if A? < B- AND B? < A+
                then A > B
                '''

                partial_understanding = len(votes[proposal1.id]['confused']) > 0 or len(votes[proposal2.id]['confused']) > 0

                # app.logger.debug("Partial Understanding for relation %s --> %s = %s",
                #     proposal1.id,
                #     proposal2.id,
                #     partial_understanding)

                if (who_dominates == endorser_ids[proposal1.id]): # newgraph
                    # dominating
                    if partial_understanding:
                        # app.logger.debug("Testing Partials A = PID %s and B = PID %s", proposal1.id, proposal2.id)
                        # app.logger.debug("Test1: A? %s < B- %s", votes[proposal1.id]['confused'], votes[proposal2.id]['oppose'])
                        # app.logger.debug("Test2: B? %s < A+ %s", votes[proposal2.id]['confused'], votes[proposal1.id]['endorse'])

                        if self.converts_to_full_domination(votes, proposal1, proposal2):
                            app.logger.debug("Partial converts...")
                            domination_map[proposal1.id][proposal2.id] = 5
                        else:
                            app.logger.debug("Partial does not convert...")
                            domination_map[proposal1.id][proposal2.id] = 3
                    else:
                        domination_map[proposal1.id][proposal2.id] = 1
                    # dominating.add(proposal2)
                elif (who_dominates == endorser_ids[proposal2.id]):
                    # dominated
                    if partial_understanding:
                        if self.converts_to_full_domination(votes, proposal2, proposal1):
                            domination_map[proposal1.id][proposal2.id] = 6
                        else:
                            domination_map[proposal1.id][proposal2.id] = 4
                    else:
                        domination_map[proposal1.id][proposal2.id] = 2
                    # dominated.add(proposal2)
                elif who_dominates == -2:
                    # both proposals have the same voters
                    domination_map[proposal1.id][proposal2.id] = -2
                else:
                    domination_map[proposal1.id][proposal2.id] = 0

                # Set second proposal based on first
                if domination_map.get(proposal2.id, None) is None:
                    domination_map[proposal2.id] = dict()
                '''
                app.logger.debug("**** Setting reverse domination_map entry [%s][%s]!!!!",
                    proposal2.id,
                    proposal1.id)
                '''
                domination_map[proposal2.id][proposal1.id] = reverse_values[domination_map[proposal1.id][proposal2.id]]

        # app.logger.debug("Complex Domination: Domination Map ==> %s", domination_map)
        return domination_map
    
    def calculate_domination_map_qualified_v1(self, generation=None, proposals=None):  
        '''
        .. function:: calculate_domination_map_qualified([generation=None])

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation. today 2
        :type generation: int
        :rtype: dict
        '''
        app.logger.debug("CALCULATE_DOMINATION_MAP_QUALIFIED CALLED...")

        generation = generation or self.generation
        app.logger.debug("calculate_domination_map_qualified: called with generation %s", generation)
        domination_map = dict()
        endorser_ids = dict()

        all_proposals = proposals or self.get_proposals_list(generation)
        
        # Get all votes sorted into sets by type for this genration
        votes = self.all_votes_by_type(generation=generation)
        app.logger.debug("votes ==> %s", votes)

        # app.logger.debug("Processing %s proposals", len(all_proposals))

        for p in all_proposals:
            endorser_ids[p.id] = p.set_of_endorser_ids(generation) # thu

        outer_counter = 0

        for proposal1 in all_proposals:
            domination_map[proposal1.id] = dict()

            outer_counter = outer_counter + 1
            # app.logger.debug("********************* OUTER PROPOSAL COUNTER = %s ********************* ", outer_counter)

            inner_counter = 0

            for proposal2 in all_proposals:
                
                inner_counter = inner_counter + 1
                # app.logger.debug("INNER PROPOSAL COUNTER = %s", inner_counter)

                if (proposal1 == proposal2):
                    domination_map[proposal1.id][proposal1.id] = -1
                    continue                
                
                # Check if the two proposals are equivalent jazz
                elif votes[proposal1.id]['oppose'] == votes[proposal2.id]['oppose'] and\
                        votes[proposal1.id]['endorse'] == votes[proposal2.id]['endorse'] and\
                        votes[proposal1.id]['confused'] == votes[proposal2.id]['confused']:
                    domination_map[proposal1.id][proposal2.id] = -1
                    continue

                qualified_voters = Proposal.\
                    intersection_of_qualfied_endorser_ids(proposal1,
                                                          proposal2,
                                                          generation)
                
                app.logger.debug("Proposal %s votes == %s", proposal1.id, endorser_ids[proposal1.id])
                app.logger.debug("Proposal %s votes == %s", proposal2.id, endorser_ids[proposal2.id])
                
                app.logger.debug("Complex Domination: qualified_voters for %s and %s ==> %s",
                    proposal1.id,
                    proposal2.id,
                    qualified_voters)

                who_dominates = Proposal.\
                    who_dominates_who_qualified(endorser_ids[proposal1.id],
                                                endorser_ids[proposal2.id],
                                                qualified_voters)
                app.logger.debug("who dominates returned ==> %s", who_dominates)

                '''
                ^ = intersection
                < = subset
                \ = set minus. (A\B= elements that are in A but not in B)
                0 = empty set.
                => = implies

                if A? < B- AND B? < A+
                then A > B
                '''

                partial_understanding = len(votes[proposal1.id]['confused']) > 0 or len(votes[proposal2.id]['confused']) > 0

                app.logger.debug("Partial Understanding for relation %s --> %s = %s",
                    proposal1.id,
                    proposal2.id,
                    partial_understanding)

                if (who_dominates == endorser_ids[proposal1.id]): # newgraph
                    # dominating
                    if partial_understanding:
                        app.logger.debug("Testing Partials A = PID %s and B = PID %s", proposal1.id, proposal2.id)
                        app.logger.debug("Test1: A? %s < B- %s", votes[proposal1.id]['confused'], votes[proposal2.id]['oppose'])
                        app.logger.debug("Test2: B? %s < A+ %s", votes[proposal2.id]['confused'], votes[proposal1.id]['endorse'])

                        if self.converts_to_full_domination(votes, proposal1, proposal2):
                            app.logger.debug("Partial converts...")
                            domination_map[proposal1.id][proposal2.id] = 5
                        else:
                            app.logger.debug("Partial does not convert...")
                            domination_map[proposal1.id][proposal2.id] = 3
                    else:
                        domination_map[proposal1.id][proposal2.id] = 1
                    # dominating.add(proposal2)
                elif (who_dominates == endorser_ids[proposal2.id]):
                    # dominated
                    if partial_understanding:
                        if self.converts_to_full_domination(votes, proposal2, proposal1):
                            domination_map[proposal1.id][proposal2.id] = 6
                        else:
                            domination_map[proposal1.id][proposal2.id] = 4
                    else:
                        domination_map[proposal1.id][proposal2.id] = 2
                    # dominated.add(proposal2)
                elif who_dominates == -2:
                    # both proposals have the same voters
                    domination_map[proposal1.id][proposal2.id] = -2
                else:
                    # Not dominated
                    domination_map[proposal1.id][proposal2.id] = 0

        # app.logger.debug("Complex Domination: Domination Map ==> %s", domination_map)
        return domination_map

    def calculate_domination_map_original(self, generation=None, proposals=None):
        '''
        .. function:: calculate_proposal_relations_original([generation=None]) today

        Calculates the complete map of dominations. For each proposal
        it calculates which dominate and which are dominated.

        :param generation: question generation.
        :type generation: int
        :rtype: dict
        '''
        app.logger.debug("calculate_domination_map_original called...")

        generation = generation or self.generation
        domination_map = dict()
        endorser_ids = dict()

        all_proposals = proposals or self.get_proposals_list(generation)
        
        for p in all_proposals:
            endorser_ids[p.id] = p.set_of_endorser_ids(generation)

        for proposal1 in all_proposals:
            domination_map[proposal1.id] = dict()

            for proposal2 in all_proposals:
                if (proposal1 == proposal2):
                    domination_map[proposal1.id][proposal1.id] = -1
                    continue
                who_dominates = Proposal.\
                    who_dominates_who(endorser_ids[proposal1.id],
                                      endorser_ids[proposal2.id])

                if (who_dominates == endorser_ids[proposal1.id]):
                    # dominating
                    domination_map[proposal1.id][proposal2.id] = 1
                    # dominating.add(proposal2)
                elif (who_dominates == endorser_ids[proposal2.id]):
                    # dominated
                    domination_map[proposal1.id][proposal2.id] = 2
                    # dominated.add(proposal2)
                elif who_dominates == -1:
                    # both proposals have the same voters
                    app.logger.debug("Simple domnateion: Both %s and %s have the same voters", proposal1.id, proposal2.id)
                    domination_map[proposal1.id][proposal2.id] = -2
                else:
                    domination_map[proposal1.id][proposal2.id] = 0

        # app.logger.debug("Simple Domination: Domination Map ==> %s", domination_map)
        return domination_map

    def calculate_pareto_front(self,
                               proposals=None,
                               exclude_user=None,
                               generation=None,
                               save=True,
                               algorithm=None):
        '''
        .. function:: calculate_pareto_front([proposals=None,
                                             exclude_user=None,
                                             generation=None,
                                             save=False,
                                             algorithm=None])

        Calculates the pareto front of the question, and optionally
        saves the dominations in the database.

        :param proposals: list of proposals
        :type proposals: list
        :param exclude_user: user to exclude from the calculation
        :type exclude_user: User
        :param generation: question generation.
        :type generation: int
        :param save: save the domination info in the DB
        :type save: boolean
        :rtype: set of proposal objects
        '''
        algorithm = algorithm or app.config['ALGORITHM_VERSION']

        app.logger.debug("calculate_pareto_front: ************ Using Algorithm %s ************", algorithm)
        app.logger.debug("calculate_pareto_front: ************ Save PF %s ************", save)

        if algorithm == 2:
            # app.logger.debug("************** USING ALGORITHM 2 ************")
            return self.calculate_pareto_front_qualified(proposals,
                                                         exclude_user,
                                                         generation,
                                                         save)
        else:
            # app.logger.debug("************** USING ALGORITHM 1 ************")
            return self.calculate_pareto_front_original(proposals,
                                                         exclude_user,
                                                         generation,
                                                         save)

    def calculate_pareto_front_qualified(self,
                               proposals=None,
                               exclude_user=None,
                               generation=None,
                               save=True):
        '''
        .. function:: calculate_pareto_front_qualified([proposals=None,
                                             exclude_user=None,
                                             generation=None,
                                             save=True])

        Calculates the pareto front of the question, and optionally
        saves the dominations in the database.

        :param proposals: list of proposals
        :type proposals: list
        :param exclude_user: user to exclude from the calculation
        :type exclude_user: User
        :param generation: question generation.
        :type generation: int
        :param save: save the domination info in the DB
        :type save: boolean
        :rtype: set of proposal objects
        '''

        app.logger.debug("calculate_pareto_front_qualified called...")
        
        save_pf = False # snow
        # Save pareto if calculated against full set of proposals and voters,
        # and save parameter not set to false
        if not exclude_user and not proposals and save:
            save_pf = True

        app.logger.debug("Save PF? - %s", save_pf)

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
                    debug("calculate_pareto_front_qualified called excluding user %s\n",
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

                    qualified_voters = Proposal.\
                        intersection_of_qualfied_endorser_ids(proposal1,
                                                              proposal2,
                                                              generation)
                    who_dominates = Proposal.\
                        who_dominates_who_qualified(props[proposal1.id],
                                                          props[proposal2.id],
                                                          qualified_voters)

                    if (who_dominates == props[proposal1.id]):
                        dominated.add(proposal2)
                        # Save PF in DB
                        if (save_pf):
                            app.logger.\
                                debug('SAVE PF: PID %s dominated_by to %s\n',
                                      proposal2.id, proposal1.id)
                            history[proposal2.id].dominated_by = proposal1.id
                    elif (who_dominates == props[proposal2.id]):
                        dominated.add(proposal1)
                        if (save_pf):
                            app.logger.\
                                debug('SAVE PF: PID %s dominated_by to %s\n',
                                      proposal2.id, proposal1.id)
                            history[proposal1.id].dominated_by = proposal2.id
                        # Proposal 1 dominated, move to next
                        break

            if (save_pf):
                db_session.commit()

            pareto = set()
            if (len(dominated) > 0):
                pareto = set(proposals) - dominated
            else:
                pareto = set(proposals)

            app.logger.debug("PARETO = %s", pareto)

            return pareto

    def calculate_pareto_front_original(self,
                               proposals=None,
                               exclude_user=None,
                               generation=None,
                               save=False):
        '''
        .. function:: calculate_pareto_front([proposals=None,
                                             exclude_user=None,
                                             generation=None,
                                             save=False,
                                             algorithm=None])

        Calculates the pareto front of the question, and optionally
        saves the dominations in the database.

        :param proposals: list of proposals
        :type proposals: list or boolean
        :param exclude_user: user to exclude from the calculation
        :type exclude_user: User
        :param generation: question generation.
        :type generation: int
        :param save: save the domination info in the DB
        :type save: boolean
        :rtype: set of proposal objects
        '''
        app.logger.debug("calculate_pareto_front_original called")
        
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
                    debug("calculate_pareto_front_original called excluding user %s\n",
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

    def get_endorser_sets(self, generation=None):
        generation = generation or self.generation
        if generation == 1:
            return set(), set()

        inherited = self.get_inherited_proposals(generation=generation)
        inherited_endorsers = self.get_endorsers_set(generation=generation-1, proposals=inherited)
        all_endorsers = self.get_endorsers_set(generation=generation-1)
        return inherited_endorsers, all_endorsers
    
    def consensus_found(self, generation=None):
        generation = generation or self.generation

        if generation == 1:
            return False

        inherited = self.get_inherited_proposals(generation=generation)
        inherited_endorsers = self.get_endorsers_set(generation=generation-1, proposals=inherited)
        all_endorsers = self.get_endorsers_set(generation=generation-1)
        return inherited_endorsers == all_endorsers
    
    def get_endorsers_set(self, generation=None, proposals=None):
        '''
        .. function:: get_endorsers([generation=None])

        Returns a set of endorsers for the current generation of
        the question.

        :param generation: question generation.
        :type generation: int
        :rtype: set
        '''
        generation = generation or self.generation

        endorsers = set()
        all_proposals = proposals or self.get_proposals(generation)
        for proposal in all_proposals:
            endorsers.update(set(proposal.endorsers(generation)))
        return endorsers
    
    def get_endorsers(self, generation=None):
        '''
        .. function:: get_endorsers([generation=None])

        Returns a set of endorsers for the current generation of
        the question.

        :param generation: question generation.
        :type generation: int
        :rtype: set
        '''
        generation = generation or self.generation

        current_endorsers = set()
        all_proposals = self.get_proposals(generation)
        for proposal in all_proposals:
            current_endorsers.update(set(proposal.endorsers(generation)))
        return current_endorsers

    def calculate_endorser_effects(self, generation=None, algorithm=None):
        '''
        .. function:: calculate_endorser_effects([generation=None, algorithm=None])

        Calculates the effects each endorser has on the pareto.
        What would be the effects if he didn't vote?
        What proposals has he forced into the pareto?

        :param generation: question generation.
        :type generation: int
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

    def calculate_key_players(self, generation=None, algorithm=None):
        '''
        .. function:: calculate_key_players([generation=None, algorithm=None])

        Calculates the effects each endorser has on the pareto.
        What would be the effects if he didn't vote?
        What proposals has he forced into the pareto?

        :param generation: question generation.
        :type generation: int
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
                key_players[user] = set()
                for users_proposal in users_pareto_proposals:
                    key_players[user].update(
                        Question.who_dominates_this_excluding(
                            users_proposal,
                            pareto,
                            user,
                            generation))
                    app.logger.debug(
                        "Pareto Props that could dominate PID %s %s\n",
                        users_proposal.id,
                        key_players[user])
            else:
                app.logger.debug("%s is not a key player\n", user.id)

        # self.save_key_players(key_players)
        app.logger.debug("Question.calc_key_players: %s", key_players)
        return key_players

    @staticmethod
    def who_dominates_this_excluding(proposal, pareto, user, generation=None, algorithm=None):
        '''
        .. function:: who_dominates_this_excluding(proposal, pareto,
                                                   user[, generation, algorithm])

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
        :type generation: int or None
        :rtype: set
        '''
        algorithm = algorithm or app.config['ALGORITHM_VERSION']

        if algorithm == 2:
            # app.logger.debug("************** USING ALGORITHM 2 ************")
            return Question.who_dominates_this_excluding_qualified(proposal,
                                                                   pareto,
                                                                   user,
                                                                   generation)
        else:
            # app.logger.debug("************** USING ALGORITHM 1 ************")
            return Question.who_dominates_this_excluding_original(proposal,
                                                                  pareto,
                                                                  user,
                                                                  generation)

    @staticmethod
    def who_dominates_this_excluding_qualified(proposal, pareto, user, generation=None, algorithm=None):
        '''
        .. function:: who_dominates_this_excluding(proposal, pareto,
                                                   user[, generation, algorithm])

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
        :type generation: int or None
        :rtype: set
        '''

        app.logger.debug("who_dominates_this_excluding_qualified\n")
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

            qualified_voters = Proposal.\
                intersection_of_qualfied_endorser_ids(proposal1,
                                                      proposal2,
                                                      generation)
            dominated = Proposal.\
                who_dominates_who_qualified(proposal_endorsers,
                                            endorsers,
                                            qualified_voters)

            # dominated = Proposal.who_dominates_who(proposal_endorsers, endorsers)

            app.logger.debug("dominated %s\n", dominated)
            if (dominated == endorsers):
                could_dominate.add(prop)
        return could_dominate

    @staticmethod
    def who_dominates_this_excluding_original(proposal, pareto, user, generation=None, algorithm=None):
        '''
        .. function:: who_dominates_this_excluding(proposal, pareto,
                                                   user[, generation, algorithm])

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
        :type generation: int or None
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

    def get_complex_voting_graph(self, generation=None):
        '''
        .. function:: get_complex_voting_graph(generation, map_type)

        Generates the svg map file from the dot string and returns the map URL.

        :param generation: the question generation
        :type generation: Integer
        :param map_type: map type
        :type map_type: string
        :rtype: string or Boolean
        '''
        # Generate filename
        '''
        filename = make_map_filename(self.id,
                                     generation,
                                     map_type,
                                     proposal_level_type,
                                     user_level_type)
        '''
        app.logger.debug("get_complex_voting_graph called.... ********** Using Algorihm 2 ************")
        algorithm = 2
        generation = generation or self.generation

        filename = make_new_map_filename_hashed(self,
                                            generation,
                                            algorithm)
        # app.logger.debug('Filename: %s hashed: %s', filename, filename_hashed)
        # filename = filename_hashed

        app.logger.debug('Filename Hashed: %s', filename)

        filepath = map_path + filename
        app.logger.debug("Filepath = %s", filepath)


        if not os.path.exists(map_path):
            try:
                os.makedirs(map_path)
            except IOError:
                app.logger.debug('Failed to create map path %s', map_path)
                return False

        # Create the SVG file if it doesn't exist
        if not os.path.isfile(filepath + '.svg'):

            # Create DOT file if it doesn't exist
            if not os.path.isfile(filepath + '.dot'):
                # Create the dot specification of the map
                app.logger.debug("dot file not found: create")
                # sick
                voting_graph = self.create_new_graph(
                    generation=generation)
                
                # Save the dot specification as a dot file
                app.logger.debug("Writing dot file %s.dot", filepath)
                dot_file = open(filepath+".dot", "w")
                dot_file.write(voting_graph.encode('utf8'))
                dot_file.close()

                if not os.path.isfile(filepath + '.dot'):
                    app.logger.debug('Failed to create dot file %s.dot',
                                     filepath)
                    return False

            else:
                app.logger.debug("%s.dot file found...", filepath)

            # Generate svg file from the dot file using "dot"
            import pydot
            graph = pydot.graph_from_dot_file(filepath+'.dot')

            # It is required on some systems to set the path to the Graphviz
            # dot file (Dreamhost, possibly because it uses Passenger)
            if app.config['GRAPHVIZ_DOT_PATH'] is not None:
                app.logger.debug('Setting Graphviz path to %s', app.config['GRAPHVIZ_DOT_PATH'])
                path = {'dot': app.config['GRAPHVIZ_DOT_PATH']}
                graph.set_graphviz_executables(path)

            graph.write_svg(filepath+'.svg')

            if not os.path.isfile(filepath + '.svg'):
                app.logger.debug('Failed to create svg file %s.svg',
                                 filepath)
                return False

        # Return voting graph file path
        return filename + ".svg"
    
    def get_voting_graph_off(self,
                         generation=None,
                         map_type='all',
                         proposal_level_type=GraphLevelType.layers,
                         user_level_type=GraphLevelType.layers,
                         algorithm=None): # oldgraph
        '''
        .. function:: get_voting_graph(generation, map_type)

        Generates the svg map file from the dot string and returns the map URL.

        :param generation: the question generation
        :type generation: Integer
        :param map_type: map type
        :type map_type: string
        :rtype: string or Boolean
        '''
        algorithm = algorithm or app.config['ALGORITHM_VERSION']

        if algorithm == 1:
            # Generate old voting graph
            return self.get_old_voting_graph(
                generation=generation,
                map_type=map_type,
                proposal_level_type=proposal_level_type,
                user_level_type=user_level_type,
                algorithm=algorithm)
        elif algorithm == 2:
            # Generate new voting graph based on Complex Algorithm
            return self.get_new_voting_graph(
                generation=generation,
                algorithm=algorithm)
        else:
            return False

    def get_voting_graph(self,
                         generation=None,
                         map_type='all',
                         proposal_level_type=GraphLevelType.layers,
                         user_level_type=GraphLevelType.layers): # oldgraph
        '''
        .. function:: get_voting_graph(generation, map_type)

        Generates the svg map file from the dot string and returns the map URL.

        :param generation: the question generation
        :type generation: Integer
        :param map_type: map type
        :type map_type: string
        :rtype: string or Boolean
        '''
        # Generate filename
        '''
        filename = make_map_filename(self.id,
                                     generation,
                                     map_type,
                                     proposal_level_type,
                                     user_level_type)
        '''
        app.logger.debug("get_voting_graph called.... ********** Using Algorihm 1 ************")
        algorithm = 1

        filename = make_map_filename_hashed(self,
                                            generation,
                                            map_type,
                                            proposal_level_type,
                                            user_level_type)
        # app.logger.debug('Filename: %s hashed: %s', filename, filename_hashed)
        # filename = filename_hashed

        app.logger.debug('Filename Hashed: %s', filename)

        filepath = map_path + filename
        app.logger.debug("Filepath = %s", filepath)

        if not os.path.exists(map_path):
            try:
                os.makedirs(map_path)
            except IOError:
                app.logger.debug('Failed to create map path %s', map_path)
                return False
        
        if not os.path.exists(work_file_dir):
            try:
                os.makedirs(work_file_dir)
            except IOError:
                app.logger.debug('Failed to create work_file_dir path %s', work_file_dir)
                return False

        # Create the SVG file if it doesn't exist
        if not os.path.isfile(filepath + '.svg'):

            # Create DOT file if it doesn't exist
            if not os.path.isfile(filepath + '.dot'):
                # Create the dot specification of the map
                app.logger.debug("dot file not found: create")
                if map_type == 'pareto':
                    app.logger.debug("Generating pareto graph...")
                    #map_proposals = self.\
                    #   get_pareto_front(generation=generation, calculate_if_missing=True)
                    map_proposals = self.calculate_pareto_front(generation=generation,
                                                                algorithm=algorithm)
                else:
                    map_proposals = self.\
                        get_proposals(generation=generation)

                app.logger.debug("Generating map with proposals...")
                app.logger.debug("DEBUG_MAP Generating map with proposals %s...", map_proposals)

                voting_graph = self.make_graphviz_map( # sick
                    proposals=map_proposals,
                    generation=generation,
                    proposal_level_type=proposal_level_type,
                    user_level_type=user_level_type,
                    algorithm=algorithm)

                # Save the dot specification as a dot file
                app.logger.debug("Writing dot file %s.dot", filepath)
                dot_file = open(filepath+".dot", "w")
                dot_file.write(voting_graph.encode('utf8'))
                dot_file.close()

                if not os.path.isfile(filepath + '.dot'):
                    app.logger.debug('Failed to create dot file %s.dot',
                                     filepath)
                    return False

            else:
                app.logger.debug("%s.dot file found...", filepath)

            # Generate svg file from the dot file using "dot"
            import pydot
            graph = pydot.graph_from_dot_file(filepath+'.dot')

            # It is required on some systems to set the path to the Graphviz
            # dot file (Dreamhost, possibly because it uses Passenger)
            if app.config['GRAPHVIZ_DOT_PATH'] is not None:
                app.logger.debug('Setting Graphviz path to %s', app.config['GRAPHVIZ_DOT_PATH'])
                path = {'dot': app.config['GRAPHVIZ_DOT_PATH']}
                graph.set_graphviz_executables(path)

            graph.write_svg(filepath+'.svg')

            if not os.path.isfile(filepath + '.svg'):
                app.logger.debug('Failed to create svg file %s.svg',
                                 filepath)
                return False

        # Return voting graph file path
        return filename + ".svg"

    def get_proposal_endorsers(self,
                               generation=None):
        generation = generation or self.generation
        proposals = self.get_proposals_list(generation)
        # app.logger.debug('get_proposal_endorsers: proposals: %s', proposals)
        proposal_endorsers = dict()
        for proposal in proposals:
            proposal_endorsers[str(proposal.id)] =\
                str(proposal.endorsers_list(generation))
        # app.logger.debug('get_proposal_endorsers: proposal_endorsers: %s', proposal_endorsers)
        return proposal_endorsers

    
    '''
    dom_map = {
    2432L: {2432L: -1, 2439L: 3, 2412L: 0, 2413L: 0, 2414L: 0, 2415L: 0, 2416L: 0, 2423L: 0}, 
    2439L: {2432L: 4, 2439L: -1, 2412L: 3, 2413L: 0, 2414L: 0, 2415L: 0, 2416L: 0, 2423L: 0}, 
    2412L: {2432L: 0, 2439L: 4, 2412L: -1, 2413L: 0, 2414L: 0, 2415L: 4, 2416L: 0, 2423L: 4}, 
    2413L: {2432L: 0, 2439L: 0, 2412L: 0, 2413L: -1, 2414L: 4, 2415L: 0, 2416L: 4, 2423L: 0}, 
    2414L: {2432L: 0, 2439L: 0, 2412L: 0, 2413L: 3, 2414L: -1, 2415L: 0, 2416L: 0, 2423L: 3}, 
    2415L: {2432L: 0, 2439L: 0, 2412L: 3, 2413L: 0, 2414L: 0, 2415L: -1, 2416L: 0, 2423L: 3}, 
    2416L: {2432L: 0, 2439L: 0, 2412L: 0, 2413L: 3, 2414L: 0, 2415L: 0, 2416L: -1, 2423L: 0}, 
    2423L: {2432L: 0, 2439L: 0, 2412L: 3, 2413L: 0, 2414L: 4, 2415L: 4, 2416L: 0, 2423L: -1}
    }
    '''
    def find_domination_cases(self, proposals, dom_map, generation): # jazz
        '''
        .. function:: find_domination_cases(
            proposals,
            dom_map,
            generation)

        Finds the domination case for each proposal.

        :param dom_map: the domination table
        :type dom_map: dict
        :param generation: the generation
        :type generation: int
        :rtype: dict
        '''
        app.logger.debug("find_domination_cases V2c called....")
        cases = dict()
        # Add for debugging
        all_dom_sets = dict()

        for proposal in proposals:
            dom_set_full = set(dom_map[proposal.id].values())
            # Remove elements not related to domination
            other_values = {-1,-2,0,1,3,5}
            dom_set = dom_set_full - other_values
            app.logger.debug("dom_set for %s = %s", proposal.id, dom_set)
            all_dom_sets[proposal.id] = dom_set

            if proposal.is_completely_understood(generation=generation):
                if not len(dom_set):
                    cases[proposal.id] = 1
                elif dom_set == {4}:
                    cases[proposal.id] = 3
                elif {2, 6} & dom_set:
                    if 4 in dom_set:
                        cases[proposal.id] = 4
                    else:
                        cases[proposal.id] = 2
                else:
                    app.logger.debug("find_domination_cases: CASE NOT SET U Proposal %s dom_set:%s ", proposal.id, dom_set)
                    cases[proposal.id] = 0
            else:
                if not len(dom_set):
                    cases[proposal.id] = 5
                elif dom_set == {4}:
                    cases[proposal.id] = 7
                elif {2, 6} & dom_set:
                    if 4 in dom_set:
                        cases[proposal.id] = 8
                    else:
                        cases[proposal.id] = 6
                else:
                    app.logger.debug("find_domination_cases: CASE NOT SET NU Proposal %s dom_set:%s ", proposal.id, dom_set)
                    cases[proposal.id] = 0

        app.logger.debug("find_domination_cases: all_dom_sets = %s", all_dom_sets)

        return cases

    def find_proposals_below(self, dom_map):
        '''
        .. function:: find_proposals_below(
            dom_map)

        Finds the proposals below each proposal on the graph

        :param dom_map: the domination table
        :type dom_map: dict
        :rtype: dict
        '''
        below = dict()

        for (pid, relations) in dom_map.iteritems():
            below[pid] = set()
            for (propid, relation) in relations.iteritems():
                if relation in {1,3,5}:
                    below[pid].add(propid)

        return below

    def create_new_graph(self, generation=None, algorithm=2): # newgraph jazz sick
        app.logger.debug("create_new_graph called: Algorithm = %s", algorithm)
        generation = generation or self.generation
        proposals = self.get_proposals_list(generation)
        all_proposals = copy.copy(proposals)
        proposals_by_id = self.get_proposals_list_by_id(generation)

        dom_map = self.calculate_domination_map(generation=generation, algorithm=algorithm)
        app.logger.debug('dom_map = %s', dom_map)
        cases = self.find_domination_cases(proposals=proposals, dom_map=dom_map, generation=generation)
        app.logger.debug('cases = %s', cases)

        relations = self.calculate_proposal_relation_ids(generation=generation, algorithm=algorithm)
        app.logger.debug("relations ==> %s", relations)
        proposals_below = dict()
        
        pareto_understood = []
        pareto_not_understood = []

        top_level = []
        graph = []
        proposals_below = dict()
        for proposal in proposals:
            proposals_below[proposal.id] = []
        
        app.logger.debug('Proposals at start = %s', proposals)

        # Step 1
        app.logger.debug("*** Step 1 ***")
        understood_undominated = []
        for prop in list(proposals):
            if len(relations[prop.id]['dominated']) == 0 and relations[prop.id]['understood']:
                top_level.append(prop.id)
                pareto_understood.append(prop.id)
                graph.append(prop.id)
                proposals_below[prop.id] = []
                proposals.remove(prop)

        notunderstood_undominated = []
        for prop in list(proposals):
            if len(relations[prop.id]['dominated']) == 0 and not relations[prop.id]['understood']:
                top_level.append(prop.id)
                pareto_not_understood.append(prop.id)
                graph.append(prop.id)
                proposals_below[prop.id] = []
                proposals.remove(prop)

        app.logger.debug('Proposals added to the Pareto in Step 1 ====> %s', graph)
        
        app.logger.debug('Proposals remaining after step 1 = %s', proposals)
        app.logger.debug('proposals_below after adding Pareto in Step 1 = %s', proposals_below)

        app.logger.debug('pareto_understood = %s', pareto_understood)
        app.logger.debug('pareto_not_understood = %s', pareto_not_understood)

        # Step 2
        step2 = []
        app.logger.debug("*** Step 2 ***")
        start_graph_len = len(graph)
        while True:
            for prop in list(proposals):
                if cases[prop.id] in [2,6,8,4]:
                    dominators = []
                    all_dominators_in_map = True
                    for (dominating_prop, relation) in dom_map[prop.id].iteritems():
                        if relation in [2,6] and dominating_prop in graph:
                            dominators.append(dominating_prop)
                        else:
                            all_dominators_in_map = False
                            break

                    if all_dominators_in_map:
                        step2.append(prop.id)
                        proposals.remove(prop)
                        for dominating_prop in dominators:
                            proposals_below[dominating_prop].append(prop.id)
                            graph.append(prop.id)

            # Quit if no new proposals were added to the graph
            if len(graph) == start_graph_len:
                break
            else:
                start_graph_len = len(graph)

        app.logger.debug("Proposals added in Step 2 ====> %s", step2)
        
        app.logger.debug('Proposals remaining after step 2 = %s', proposals)
        app.logger.debug('Graph after Step 2 = %s', graph)

        adding = []
        # Step 3 - Add partially dominated all in one go
        app.logger.debug("*** Step 3 ***")
        for prop in list(proposals):
            app.logger.debug("Step 3: Looking at proposal %s", prop.id)
            if cases[prop.id] in [3,7]:
                for (dominating_prop, relation) in dom_map[prop.id].iteritems():
                    if relation == 4 and dominating_prop in graph:
                        app.logger.debug('Adding proposal %s below %s', prop.id, dominating_prop)
                        proposals_below[dominating_prop].append(prop.id)
                        adding.append(prop.id)

        app.logger.debug("Proposals added in Step 3 ====> %s", adding)
        graph = graph + adding

        for prop in list(proposals):
            if prop.id in adding:
                app.logger.debug('Removing prop %s from remaining proposals %s', prop.id, proposals)
                proposals.remove(prop)
                app.logger.debug('Remaining roposals now %s', proposals)

        app.logger.debug('Proposals remaining after step 3 = %s', proposals)
        app.logger.debug('Graph after Step 3 = %s', proposals_below)

        # Step 4
        step4 = []
        app.logger.debug("*** Step 4 ***")
        for prop in list(proposals):
            if cases[prop.id] in [3,7]:
                graph.append(prop.id)
                step4.append(prop.id)
                proposals_below[prop.id] = []
        app.logger.debug("Proposals added in Step 4 ====> %s", step4)
        
        # Step 5
        app.logger.debug("*** Step 5 ***")
        step5 = []
        start_graph_len = len(graph)
        app.logger.debug("Beginning Step 5 with %s proposals left", start_graph_len)
        while True:
            for prop in list(proposals):
                if cases[prop.id] in [2,6,8,4]:
                    dominators = []
                    all_dominators_in_map = True
                    for (dominating_prop, relation) in dom_map[prop.id].iteritems():
                        if relation in [2,6]:
                            if dominating_prop in graph:
                                dominators.append(dominating_prop)
                            else:
                                all_dominators_in_map = False
                                break

                    if all_dominators_in_map:
                        step5.append(prop.id)
                        proposals.remove(prop)
                        for dominating_prop in dominators:
                            proposals_below[dominating_prop].append(prop.id)
                            graph.append(prop.id)

            # Quit if no new proposals were added to the graph
            if len(graph) == start_graph_len:
                break
            else:
                start_graph_len = len(graph)
        app.logger.debug("Proposals added in Step 5 ====> %s", step5)
        
        # Step 6 - Add remaining to the pareto front
        app.logger.debug("*** Step 6 ***")
        step6 = []
        for prop in list(proposals):
            graph.append(prop.id)
            step6.append(prop.id)
            
            if relations[prop.id]['understood']:
                pareto_understood.append(prop.id)
            else:
                pareto_not_understood.append(prop.id)
            
            proposals_below[prop.id] = []
            proposals.remove(prop)

        app.logger.debug("Proposals added in Step 6 ====> %s", step6)

        # return proposals_below

        app.logger.debug("final proposals_below ==> %s", proposals_below) # jazz

        proposals_covered = self.get_covered_complex(proposals_below)
        app.logger.debug("proposals_covered ==> %s", proposals_covered)

        proposal_levels = self.find_levels_complex(proposals_covered)
        app.logger.debug("proposal_levels ==> %s", proposal_levels)

        proposal_levels_keys = proposal_levels.keys()
        app.logger.debug("proposal_levels_keys ==> %s", proposal_levels_keys)

        # Begin creation of Graphviz string
        title = self.string_safe(self.title)
        voting_graph = 'digraph "%s" {\n' % (title)

        for l in proposal_levels_keys:
            voting_graph += ' "pl' + str(l) +\
                '" [shape=point fontcolor=white ' +\
                'color=white fontsize=1]; \n'

        for l in proposal_levels_keys:
            if (l != proposal_levels_keys[0]):
                voting_graph += ' -> '
            voting_graph += '"pl' + str(l) + '" '

        voting_graph += " [color=white] \n "

        for l in proposal_levels_keys:
            voting_graph += '{rank=same; "pl' + str(l) + '" '
            for p in proposal_levels[l]:
                voting_graph += " " + str(proposals_by_id[p].id) + " "
            voting_graph += "}\n"

        for p in all_proposals:
            color = "black"
            peripheries = 1

            if p.id in pareto_understood:
                fillcolor = '"lightblue" '
            elif p.id in pareto_not_understood:
                fillcolor = '"lightcyan" '
            else:
                fillcolor = '"white" '
            
            tooltip = self.create_proposal_tooltip(p)
            app.logger.debug("tootltip = %s", tooltip)
            
            voting_graph += str(p.id) +\
                ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                ' shape=box fillcolor=' + fillcolor +\
                ' style=filled color=' + color + ' peripheries=' +\
                str(peripheries) + ' tooltip="' + tooltip +\
                '"  fontsize=11]'

            '''
            if p.id in pareto_understood or p.id in pareto_not_understood or p.id in step6:
                voting_graph += str(p.id) +\
                    ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                    ' shape=box fillcolor=' + fillcolor +\
                    ' style=filled color=' + color + ' peripheries=' +\
                    str(peripheries) + ' tooltip="' + tooltip +\
                    '"  fontsize=11]'
            else:
                voting_graph += str(p.id) +\
                    ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                    ' shape=box fillcolor="white" style="filled" color=' + color + ' peripheries=' +\
                    str(peripheries) + ' tooltip="' + tooltip +\
                    '"  fontsize=11]'
            '''

        edge_type = {'full': 'normal', 'partial': 'onormal'}

        for proposal in all_proposals:
            pcolor = "black"

            pcs = proposals_covered[proposal.id]
            for pc in pcs:
                color = pcolor

                left_prop_id = 'p' + str(proposals_by_id[pc].id)
                right_prop_id = 'p' + str(proposal.id)
                
                # app.logger.debug("Check dom type for drawing arrowhead for proposal %s ==> %s", proposal.id, dom_map[proposal.id][pc])
                
                if dom_map[proposal.id][pc] in [3,4]:
                    dom_type = 'partial'
                else:
                    dom_type = 'full'

                edge_id = 'id="' + left_prop_id + '&#45;&#45;' +\
                    right_prop_id + '"'

                #voting_graph += ' ' + str(proposals_by_id[pc].id) + ' -> ' + str(proposal.id) +\
                #    ' [' + edge_id + ' class="edge" color="' + color + '" arrowhead="' + edge_type[dom_type] + '"]'
                
                # Change arrows to point in the direction of the domination
                #
                voting_graph += ' ' + str(proposal.id) + ' -> ' +  str(proposals_by_id[pc].id)  +\
                    ' [' + edge_id + ' class="edge" color="' + color + '" arrowhead="' + edge_type[dom_type] + '"]'
                
                voting_graph += " \n"

        voting_graph += "\n}"

        return voting_graph


    # the newgraph 
    def make_new_graphviz_map_off(self,
                          proposals=None,
                          generation=None,
                          algorithm=None):
        '''
        .. function:: make_new_graphviz_map(
            [proposals=None,
            generation=None,
            algorithm=None])

        Generates the string to create a voting graph from Graphviz.

        :param proposals: set of proposals
        :type proposals: set or None
        :param generation: the generation
        :type generation: int or None
        :param algorithm: the algorithm to use
        :type algorithm: int or None
        :rtype: string
        '''
        generation = generation or self.generation

        # get set of all proposals -- debugging
        proposals = proposals or self.get_proposals(generation)
        app.logger.debug("DEBUG_MAP create map using proposals %s in generation %s\n",
                         proposals, generation)

        proposal_ids = get_ids_from_proposals(proposals)
        app.logger.debug("DEBUG_MAP: map pids %s", proposal_ids)

        # get pareto
        pareto = self.calculate_pareto_front(proposals=proposals,
                                             generation=generation,
                                             algorithm=algorithm)
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
                endorser.get_endorsed_proposal_ids_new(self, generation, proposal_ids) # fix?
        app.logger.debug("endorser_proposals %s\n",
                         endorser_proposals)

        # get dict of pareto proposals => endorsers
        pareto_endorsers = dict()
        for proposal in pareto:
            pareto_endorsers[proposal.id] = proposal.endorsers(generation)
        app.logger.debug("pareto proposals => endorsers %s\n",
                         pareto_endorsers)

        proposal_relations = self.calculate_proposal_relations(generation=generation,
                                                               proposals=proposals,
                                                               algorithm=algorithm) # algstuff
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

        proposals_covered = self.get_covered(proposals_below, proposals) # hereiam
        app.logger.debug("proposals_covered %s\n",
                         proposals_covered)

        if (proposal_level_type == GraphLevelType.num_votes):
            proposal_levels = self.find_levels_based_on_size(
                proposal_endorsers)
        elif (proposal_level_type == GraphLevelType.layers):
            proposal_levels = self.find_levels(proposals_covered, proposals)
        else:
            proposal_levels = list()
            proposal_levels[0] = proposals

        app.logger.debug("***proposal_levels %s\n",
                         proposal_levels)

        # debugging
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

        proposal_levels_keys = proposal_levels.keys()

        # Begin creation of Graphviz string
        title = self.string_safe(self.title)
        voting_graph = 'digraph "%s" {\n' % (title) # hereiam

        for l in proposal_levels_keys:
            voting_graph += ' "pl' + str(l) +\
                '" [shape=point fontcolor=white ' +\
                'color=white fontsize=1]; \n'

        for l in proposal_levels_keys:
            if (l != proposal_levels_keys[0]):
                voting_graph += ' -> '
            voting_graph += '"pl' + str(l) + '" '

        voting_graph += " [color=white] \n "

        for l in proposal_levels_keys:
            voting_graph += '{rank=same; "pl' + str(l) + '" '
            for p in proposal_levels[l]:
                if (p in bundled_proposals):
                    continue
                voting_graph += " " + str(p.id) + " "
            voting_graph += "}\n"


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

                app.logger.debug("DEBUG_MAP: endo = %s", endo)
                app.logger.debug("DEBUG_MAP: endorsers = %s", endorsers)
                
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
                app.logger.debug("DEBUG_MAP: p = %s", p)
                endo = p.endorsers(generation)

                app.logger.debug("DEBUG_MAP: endo = %s", endo)
                app.logger.debug("DEBUG_MAP: endorsers = %s", endorsers)
                
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
                        '"  fontsize=11]'
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
                    tooltip = self.create_proposal_tooltip(p)
                    voting_graph += str(p.id) +\
                        ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                        ' shape=box fillcolor="white" style="filled" color=' + color + ' peripheries=' +\
                        str(peripheries) + ' tooltip="' +\
                        tooltip +\
                        '"  fontsize=11]'
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

                if (highlight_user1 and highlight_user1 in proposal_endorsers[pc]):
                    color = "red"

                # An empty array is trivially dominated by everything.
                #
                # But that is so trivial that it simplifies the graph
                # if we just do not show those lines.
                if (pc in proposal_endorsers and len(proposal_endorsers[pc]) == 0):
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

                edge_id = 'id="' + left_prop_id + '&#45;&#45;' +\
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

                #
                # Calculate left and right user ids
                #
                left_usernode_id = self.calculate_user_node_id(
                    e,
                    combined_users)

                right_usernode_id = self.calculate_user_node_id(
                    ec,
                    combined_users)

                if e.id == 2:
                    app.logger.debug("left_usernode_id ==> %s", left_usernode_id)
                    app.logger.debug("right_usernode_id ==> %s", right_usernode_id)

                # edge_id = 'id="u' + str(e.id) + '&#45;&#45;' +\
                #    'u' + str(ec.id) + '"'
                
                edge_id = 'id="' + left_usernode_id + '&#45;&#45;' +\
                    right_usernode_id + '"'

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

                usernode_id = self.calculate_user_node_id(
                    e,
                    combined_users)

                propnode_id = self.calculate_propsal_node_id(
                    p,
                    combined_proposals)

                # if p.id == 1:
                #    app.logger.debug("propnode_id ==> %s", propnode_id)
                #    app.logger.debug("usernode_id ==> %s", usernode_id)

                # edge_id = 'id="u' + str(e.id) + '&#45;&#45;' +\
                #    propnode_id + '"'

                edge_id = 'id="' + usernode_id + '&#45;&#45;' +\
                    propnode_id + '"'

                voting_graph += ' "' + e.username + '" -> ' + str(p.id) +\
                    ' [' + edge_id + ' class="edge" color="' + color + '"]'
                voting_graph += " \n"

        voting_graph += "\n}"

        return voting_graph
    
    # oldgraph
    def make_graphviz_map_plain(self,
                          proposals=None,
                          generation=None,
                          proposal_level_type=GraphLevelType.layers,
                          user_level_type=GraphLevelType.layers,
                          algorithm=None):
        '''
        .. function:: make_graphviz_map_plain(
            [proposals=None,
            generation=None,
            proposal_level_type=GraphLevelType.layers,
            user_level_type=GraphLevelType.layerss])

        Generates the string to create a voting graph from Graphviz.
        This version does not personalise the graph for each user -
        this is now done at the front end.

        :param proposals: set of proposals
        :type proposals: set or None
        :param generation: the generation
        :type generation: int or None
        :param proposal_level_type: required layout of user nodes
        :type proposal_level_type: GraphLevelType
        :param user_level_type: required layout of user nodes
        :type user_level_type: GraphLevelType
        :rtype: string
        '''
        app.logger.debug("make_graphviz_map_plain called....")
        
        generation = generation or self.generation

        # get set of all proposals -- debugging
        proposals = proposals or self.get_proposals(generation)
        app.logger.debug("DEBUG_MAP create map using proposals %s in generation %s\n",
                         proposals, generation)

        proposal_ids = get_ids_from_proposals(proposals)
        app.logger.debug("DEBUG_MAP: map pids %s", proposal_ids)

        # get pareto
        pareto = self.calculate_pareto_front(proposals=proposals,
                                             generation=generation,
                                             algorithm=algorithm)
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
                endorser.get_endorsed_proposal_ids_new(self, generation, proposal_ids) #
        app.logger.debug("endorser_proposals %s\n",
                         endorser_proposals)

        # get dict of pareto proposals => endorsers
        pareto_endorsers = dict()
        for proposal in pareto:
            pareto_endorsers[proposal.id] = proposal.endorsers(generation)
        app.logger.debug("pareto proposals => endorsers %s\n",
                         pareto_endorsers)

        proposal_relations = self.calculate_proposal_relations(generation=generation,
                                                               proposals=proposals,
                                                               algorithm=algorithm) # algstuff
        app.logger.debug("proposal_relations %s\n",
                         proposal_relations)

        proposals_below = dict() #oldgraph
        for (proposal, relation) in proposal_relations.iteritems():
            proposals_below[proposal] = relation['dominating']
        app.logger.debug("proposals_below %s\n",
                         proposals_below)

        proposals_covered = self.get_covered(proposals_below, proposals) #here
        app.logger.debug("proposals_covered %s\n",
                         proposals_covered)

        # Endorser relations
        endorser_relations = self.calculate_endorser_relations_2(proposals=proposals, generation=generation)
        app.logger.debug("DEBUG_MAP:: endorser_relations %s\n",
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

        if (proposal_level_type == GraphLevelType.num_votes):
            proposal_levels = self.find_levels_based_on_size(
                proposal_endorsers)
        elif (proposal_level_type == GraphLevelType.layers):
            proposal_levels = self.find_levels(proposals_covered, proposals)
        else:
            proposal_levels = list()
            proposal_levels[0] = proposals

        app.logger.debug("***proposal_levels %s\n",
                         proposal_levels)

        if (user_level_type == GraphLevelType.num_votes):
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

        # debugging
        combined_proposals = self.combine_proposals( # hereiam
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



        # Bundle Users
        app.logger.debug("DEBUG_MAP: proposal_endorsers = %s", proposal_endorsers)
        app.logger.debug("DEBUG_MAP: endorsers = %s", endorsers)
        
        combined_users = self.combine_users(
            proposal_endorsers, endorsers, generation, proposals)
            
        app.logger.debug("DEBUG_MAP: combined_users = %s", combined_users)

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

        # Begin creation of Graphviz string
        title = self.string_safe(self.title)
        voting_graph = 'digraph "%s" {\n' % (title)

        for l in proposal_levels_keys:
            voting_graph += ' "pl' + str(l) +\
                '" [shape=point fontcolor=white ' +\
                'color=white fontsize=1]; \n'

        for l in user_levels_keys:
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

            details_table = ' BGCOLOR="lightpink3" '
            details = ' fillcolor=white style=filled color=' +\
                color + ' peripheries=' + str(peripheries) + ' '

            voting_graph += self.write_bundled_users(
                kc2u.username,
                combined_users[kc2u],
                self.room,
                details,
                details_table)

        for e in endorsers:
            if (e in bundled_users or e in combined_users):
                continue

            color = "lightpink3"
            fillcolor = "lightpink3"
            peripheries = 0

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

                app.logger.debug("DEBUG_MAP: endo = %s", endo)
                app.logger.debug("DEBUG_MAP: endorsers = %s", endorsers)
                
                if (len(endo) == len(endorsers)):
                    details_table = ' BGCOLOR="gold" '
                else:
                    details_table = ' BGCOLOR="lightblue" '

                details = ' fillcolor=white style=filled color=' + color +\
                    ' peripheries=' + str(peripheries) + ' '
            else:
                color = "black"
                peripheries = 0

                details = ' fillcolor=white color=' + color +\
                    ' peripheries=' + str(peripheries) + ' '

            voting_graph += self.write_bundled_proposals(
                kc2p.id, combined_proposals[kc2p], self.room,
                details,
                details_table)

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

            if (p in pareto):
                app.logger.debug("DEBUG_MAP: p = %s", p)
                endo = p.endorsers(generation)

                app.logger.debug("DEBUG_MAP: endo = %s", endo)
                app.logger.debug("DEBUG_MAP: endorsers = %s", endorsers)
                
                if (len(endo) == len(endorsers)):
                    fillcolor = '"gold"'
                else:
                    fillcolor = '"lightblue" '

                urlquery = self.create_proposal_url(p, self.room)
                tooltip = self.create_proposal_tooltip(p)
                voting_graph += str(p.id) +\
                    ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                    ' shape=box fillcolor=' + fillcolor +\
                    ' style=filled color=' + color + ' peripheries=' +\
                    str(peripheries) + ' tooltip="' + tooltip +\
                    '"  fontsize=11]'


            else:
                urlquery = self.create_proposal_url(p, self.room)
                tooltip = self.create_proposal_tooltip(p)
                voting_graph += str(p.id) +\
                    ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                    ' shape=box fillcolor="white" style="filled" color=' + color + ' peripheries=' +\
                    str(peripheries) + ' tooltip="' +\
                    tooltip +\
                    '"  fontsize=11]'

        for p in proposals:
            pcolor = "black"
            if (p in bundled_proposals):
                continue

            pcs = proposals_covered[p]
            for pc in pcs:
                color = pcolor
                if (pc in bundled_proposals):
                    continue

                # An empty array is trivially dominated by everything.
                #
                # But that is so trivial that it simplifies the graph
                # if we just do not show those lines.
                if (pc in proposal_endorsers and len(proposal_endorsers[pc]) == 0):
                    color = "white"


                left_prop_id = self.calculate_propsal_node_id(
                    pc,
                    combined_proposals)
                right_prop_id = self.calculate_propsal_node_id(
                    p,
                    combined_proposals)

                edge_id = 'id="' + left_prop_id + '&#45;&#45;' +\
                    right_prop_id + '"'

                voting_graph += ' ' + str(pc.id) + ' -> ' + str(p.id) +\
                    ' [' + edge_id + ' class="edge" color="' + color + '"]'
                voting_graph += " \n"

        for e in endorsers:
            ecolor = "blue"
            if (e in bundled_users):
                continue

            ecs = endorsers_covered[e]

            for ec in ecs:
                color = ecolor
                if (ec in bundled_users):
                    continue

                #
                # Calculate left and right user ids
                #
                left_usernode_id = self.calculate_user_node_id(
                    e,
                    combined_users)

                right_usernode_id = self.calculate_user_node_id(
                    ec,
                    combined_users)

                if e.id == 2:
                    app.logger.debug("left_usernode_id ==> %s", left_usernode_id)
                    app.logger.debug("right_usernode_id ==> %s", right_usernode_id)
                
                edge_id = 'id="' + left_usernode_id + '&#45;&#45;' +\
                    right_usernode_id + '"'

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

                usernode_id = self.calculate_user_node_id(
                    e,
                    combined_users)

                propnode_id = self.calculate_propsal_node_id(
                    p,
                    combined_proposals)

                edge_id = 'id="' + usernode_id + '&#45;&#45;' +\
                    propnode_id + '"'

                voting_graph += ' "' + e.username + '" -> ' + str(p.id) +\
                    ' [' + edge_id + ' class="edge" color="' + color + '"]'
                voting_graph += " \n"

        voting_graph += "\n}"

        return voting_graph
    
    # newgraph
    def make_graphviz_map(self,
                          proposals=None,
                          generation=None,
                          internal_links=False,
                          proposal_level_type=GraphLevelType.layers,
                          user_level_type=GraphLevelType.layers,
                          address_image='',
                          highlight_user1=None,
                          highlight_proposal1=None,
                          algorithm=None):
        '''
        .. function:: make_graphviz_map(
            [proposals=None,
            generation=None,
            internal_links=False,
            proposal_level_type=GraphLevelType.layers,
            user_level_type=GraphLevelType.layerss,
            address_image='',
            highlight_user1=None,
            highlight_proposal1=None],
            algorithm=None)

        Generates the string to create a voting graph from Graphviz.

        :param proposals: set of proposals
        :type proposals: set or None
        :param generation: the generation
        :type generation: int or None
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
        algorithm = algorithm or app.config['ALGORITHM_VERSION'] # sick
        app.logger.debug("make_graphviz_map: *********** Using Algorithm %s **********", algorithm)

        # get set of all proposals -- debugging
        proposals = proposals or self.get_proposals(generation)
        # app.logger.debug("DEBUG_MAP create map using proposals %s in generation %s\n",
        #                  proposals, generation)

        proposal_ids = get_ids_from_proposals(proposals)
        # app.logger.debug("DEBUG_MAP: map pids %s", proposal_ids)

        # get pareto
        app.logger.debug("make_graphviz_map: Get Pareto Front")
        pareto = self.calculate_pareto_front(proposals=proposals,
                                             generation=generation,
                                             algorithm=algorithm)
        # app.logger.debug("pareto %s\n", pareto)

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
                endorser.get_endorsed_proposal_ids_new(self, generation, proposal_ids) # fix?
        app.logger.debug("endorser_proposals %s\n",
                         endorser_proposals)

        # get dict of pareto proposals => endorsers
        pareto_endorsers = dict()
        for proposal in pareto:
            pareto_endorsers[proposal.id] = proposal.endorsers(generation)
        app.logger.debug("pareto proposals => endorsers %s\n",
                         pareto_endorsers)

        proposal_relations = self.calculate_proposal_relations(generation=generation,
                                                               proposals=proposals,
                                                               algorithm=algorithm) # algstuff
        app.logger.debug("proposal_relations %s\n",
                         proposal_relations)

        proposals_below = dict() #oldgraph jazz
        proposals_above = dict()
        for (proposal, relation) in proposal_relations.iteritems():
            proposals_below[proposal] = relation['dominating']
            proposals_above[proposal] = relation['dominated']
        app.logger.debug("proposals_above ==> %s\n",
                         proposals_above)
        
        app.logger.debug("proposals_below ==> %s\n",
                         proposals_below)

        proposals_covered = self.get_covered(proposals_below, proposals)
        app.logger.debug("proposals_covered ==> %s\n",
                         proposals_covered)

        # Endorser relations
        endorser_relations = self.calculate_endorser_relations_2(proposals=proposals, generation=generation)
        app.logger.debug("DEBUG_MAP:: endorser_relations %s\n",
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

        if (proposal_level_type == GraphLevelType.num_votes):
            proposal_levels = self.find_levels_based_on_size(
                proposal_endorsers)
        elif (proposal_level_type == GraphLevelType.layers):
            proposal_levels = self.find_levels(proposals_covered, proposals)
        else:
            proposal_levels = list()
            proposal_levels[0] = proposals

        app.logger.debug("***proposal_levels %s\n",
                         proposal_levels)

        if (user_level_type == GraphLevelType.num_votes):
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

        # debugging
        combined_proposals = self.combine_proposals( # hereiam
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



        # Bundle Users
        app.logger.debug("DEBUG_MAP: proposal_endorsers = %s", proposal_endorsers)
        app.logger.debug("DEBUG_MAP: endorsers = %s", endorsers)
        
        combined_users = self.combine_users(
            proposal_endorsers, endorsers, generation, proposals)
            
        app.logger.debug("DEBUG_MAP: combined_users = %s", combined_users)

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

        # Begin creation of Graphviz string
        title = self.string_safe(self.title)
        voting_graph = 'digraph "%s" {\n' % (title)

        for l in proposal_levels_keys:
            voting_graph += ' "pl' + str(l) +\
                '" [shape=point fontcolor=white ' +\
                'color=white fontsize=1]; \n'

        for l in user_levels_keys:
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
                self.room,
                details,
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

                app.logger.debug("DEBUG_MAP: endo = %s", endo)
                app.logger.debug("DEBUG_MAP: endorsers = %s", endorsers)
                
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
                app.logger.debug("DEBUG_MAP: p = %s", p)
                endo = p.endorsers(generation)

                app.logger.debug("DEBUG_MAP: endo = %s", endo)
                app.logger.debug("DEBUG_MAP: endorsers = %s", endorsers)
                
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
                        '"  fontsize=11]'
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
                    tooltip = self.create_proposal_tooltip(p)
                    voting_graph += str(p.id) +\
                        ' [id=p' + str(p.id) + ' label=' + str(p.id) +\
                        ' shape=box fillcolor="white" style="filled" color=' + color + ' peripheries=' +\
                        str(peripheries) + ' tooltip="' +\
                        tooltip +\
                        '"  fontsize=11]'
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

                if (highlight_user1 and highlight_user1 in proposal_endorsers[pc]):
                    color = "red"

                # An empty array is trivially dominated by everything.
                #
                # But that is so trivial that it simplifies the graph
                # if we just do not show those lines.
                if (pc in proposal_endorsers and len(proposal_endorsers[pc]) == 0):
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

                edge_id = 'id="' + left_prop_id + '&#45;&#45;' +\
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

                #
                # Calculate left and right user ids
                #
                left_usernode_id = self.calculate_user_node_id(
                    e,
                    combined_users)

                right_usernode_id = self.calculate_user_node_id(
                    ec,
                    combined_users)

                if e.id == 2:
                    app.logger.debug("left_usernode_id ==> %s", left_usernode_id)
                    app.logger.debug("right_usernode_id ==> %s", right_usernode_id)

                # edge_id = 'id="u' + str(e.id) + '&#45;&#45;' +\
                #    'u' + str(ec.id) + '"'
                
                edge_id = 'id="' + left_usernode_id + '&#45;&#45;' +\
                    right_usernode_id + '"'

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

                usernode_id = self.calculate_user_node_id(
                    e,
                    combined_users)

                propnode_id = self.calculate_propsal_node_id(
                    p,
                    combined_proposals)

                # if p.id == 1:
                #    app.logger.debug("propnode_id ==> %s", propnode_id)
                #    app.logger.debug("usernode_id ==> %s", usernode_id)

                # edge_id = 'id="u' + str(e.id) + '&#45;&#45;' +\
                #    propnode_id + '"'

                edge_id = 'id="' + usernode_id + '&#45;&#45;' +\
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
        app.logger.debug("calculate_user_node_id for user %s", user.id)
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
        '''
        app.logger.debug("new_endorsers_to_a_proposal....\n")
        app.logger.debug("proposal INSIDE ==> %s\n", proposal)
        app.logger.debug("proposal_endorsers INSIDE ==> %s\n",
                         proposal_endorsers)
        app.logger.debug("proposals_covered INSIDE ==> %s\n",
                         proposals_covered)

        below = proposals_covered[proposal]
        # app.logger.debug("below INSIDE ==> %s\n", below)

        voters_known = set()
        for b in below:
            '''
            app.logger.debug("proposal_endorsers[b] INSIDE ==> %s\n",
                proposal_endorsers[b])
            '''
            if b in proposal_endorsers:
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
                bundle += '<TD ' + to_add +\
                    ' tooltip="' + tooltip + '">' +\
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
            node_id += 'u' + str(user.id)

        # app.logger.debug("write_bundled_users...")
        # app.logger.debug("node_id ===> %s", node_id)
        # app.logger.debug("bundle_name == %s", bundle_name)

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
            bundle += '<TR><TD ' + to_add + ' HREF="http://' +\
                app.config['SITE_DOMAIN'] +\
                '/user+php?u=' +\
                urlquery + '" tooltip="' + tooltip + '" target="_top">' +\
                u.username + '</TD></TR>'

        for u in bundle_content:
            # This has already been written
            if (highlight_user1 and highlight_user1 == u):
                continue

            urlquery = str(u.id)
            tooltip = u.username
            bundle += '<TR><TD ' +\
                'tooltip="' + tooltip + '" target="' + str(u.id) + '">' +\
                u.username + '</TD></TR>'

        bundle += '</TABLE>>]'
        bundle += "\n"
        app.logger.debug("bundled_users ==> %s", bundle)
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
        if (proposal.abstract and len(proposal.abstract) > 0):
            tooltip = self.string_safe(proposal.abstract)
        else:
            tooltip = self.string_safe(proposal.blurb)
        return tooltip[:800]

    def create_internal_proposal_url(self, proposal):
        return "#proposal" + str(proposal.id)

    def create_proposal_url(self, proposal, room):
        return str(proposal.id) + '/' + room

    def get_elements_covered(self, elements_below): 
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
        elements = elements_below.keys()
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
    
    def get_covered(self, elements_below, elements): # jazz
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

    def get_covered_complex(self, elements_below): 
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
        elements = set(elements_below.keys())
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

    def find_levels_complex(self, elements_covered): # hereiam
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

        elements = set(elements_covered.keys())
        elements_to_test = copy.copy(elements)
        
        app.logger.debug("find_levels called...\n")
        app.logger.debug("elements_covered => %s", elements_covered)
        app.logger.debug("elements => %s", elements)
        
        
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
    
    def find_levels(self, elements_covered, elements): # hereiam
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
        app.logger.debug("find_levels called...\n")
        app.logger.debug("elements_covered => %s", elements_covered)
        app.logger.debug("elements => %s", elements)

        elements = set(elements)
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

        if (not proposals):
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



    def combine_users(self, proposal_endorsers, endorsers, generation, proposals):
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
                    endorser1.get_endorsed_proposal_ids_2(self, proposals, generation))
                app.logger.debug(
                    "endorser2 endorsed %s\n",
                    endorser2.get_endorsed_proposal_ids_2(self, proposals, generation))

                if (endorser1.get_endorsed_proposal_ids_2(self, proposals, generation) ==
                        endorser2.get_endorsed_proposal_ids_2(self, proposals, generation)):
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

    def combine_users_ver1(self, proposal_endorsers, endorsers, generation):
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


class KeyPlayer(db.Model):
    '''
    Stores key player information for each geenration
    '''
    __tablename__ = "key_player"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    generation = db.Column(db.Integer)

    proposal = db.relationship("Proposal", single_parent=True)
    user = db.relationship("User", single_parent=True)

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


class Comment(db.Model):
    '''
    Holds comments made during voting when a user opposes a proposal or
    does not understand one.
    '''

    __tablename__ = 'comment'

    def get_public(self):
        '''
        .. function:: get_public()

        Return public propoerties as string values for REST responses.

        :rtype: dict
        '''
        supporters = self.fetch_supporter_ids()

        return {'id': str(self.id),
                'url': url_for('api_get_proposal_comments',
                               question_id=self.question_id,
                               proposal_id=self.proposal_id,
                               comment_id=self.id),
                'comment': self.comment,
                'comment_type': self.comment_type,
                'reply_to': str(self.reply_to),
                'generation': str(self.generation),
                'created': str(self.created),
                'author_id': str(self.user_id),
                'author_url': url_for('api_get_users', user_id=self.user_id),
                'proposal_url': url_for('api_get_question_proposals',
                                        question_id=self.question_id,
                                        proposal_id=self.proposal_id),
                'question_url': url_for('api_get_questions',
                                        question_id=self.question_id),
                'supporters': str(supporters)}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    generation = db.Column(db.Integer)
    created = db.Column(db.DateTime)
    comment = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.Enum('for', 'against', 'question', 'answer', name="comment_type_enum"),
                             nullable=False)
    reply_to =  db.Column(db.Integer, default=0)

    def __init__(self, user, proposal, comment, comment_type, reply_to=0):
        self.user_id = user.id
        self.proposal_id = proposal.id
        self.question_id = proposal.question.id
        self.generation = proposal.question.generation
        self.created = datetime.datetime.utcnow()
        self.comment = comment
        self.comment_type = comment_type
        self.reply_to = reply_to

    def fetch_supporter_ids(self):
        user_list = self.supporters.all()
        # app.logger.debug("fetch_supporter_ids: user_list = %s", user_list)
        ids = list()
        for user in user_list:
            ids.append(int(user.id))
        # app.logger.debug("fetch_supporter_ids: ids returned = %s", ids)
        return ids

    @staticmethod
    def fetch_if_exists(proposal, comment, comment_type, generation=None):
        '''
        .. function:: fetch_if_exists(proposal, comment, comment_type[, generation])

        Returns the comment which matches new_comment,
            or False if no match.

        :param proposal: proposal
        :type comment: Proposal
        :param comment: comment text
        :type comment: string
        :param comment_type: type of comment
        :type comment_type: string
        :param generation: generation qustion was asked
        :type generation: int or None
        :rtype: Comment or boolean
        '''
        generation = generation or proposal.question.generation
        existing_comment = db_session.query(Comment).filter(and_(
            Comment.proposal_id == proposal.id,
            Comment.generation == generation,
            Comment.comment_type == comment_type,
            Comment.comment == comment)
        ).first()
        if (existing_comment):
            return existing_comment
        else:
            return False


class QuestionHistory(db.Model):
    '''
    Represents the QuestionHistory object which holds the historical
    proposal data for the question.

    Proposal data is copied here when the question is moved on to
    the writing stage.
    '''

    __tablename__ = 'question_history'

    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    generation = db.Column(db.Integer)
    dominated_by = db.Column(db.Integer, nullable=False, default=0)

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


class Proposal(db.Model):
    '''
    Represents the proposal object
    '''

    __tablename__ = 'proposal'

    def __repr__(self):
        return "<Proposal(%s '%s' by %s, Q:'%s')>"\
            % (self.id,
               self.title,
               self.author.username,
               self.question_id)

    def get_public(self, user=None):
        '''
        .. function:: get_public()

        Return public propoerties as string values for REST responses.

        :rtype: dict
        '''
        num_votes = self.get_vote_count()
        public = {'id': str(self.id),
                'uri': url_for('api_get_question_proposals',
                               question_id=self.question.id,
                               proposal_id=self.id),
                'title': self.title,
                'blurb': self.blurb,
                'abstract': self.abstract,
                'generation_created': str(self.generation_created),
                'source': str(self.source),
                'created': str(self.created),
                'author': self.author.username,
                'question_count': str(self.get_question_count()),
                'comment_count': str(self.get_comment_count()),
                'vote_count': str(num_votes),
                'author_id': str(self.author.id),
                'geomedy': str(self.geomedx),
                'geomedy': str(self.geomedy),
                'author_url': url_for('api_get_users', user_id=self.user_id),
                'question_url': url_for('api_get_questions',
                                        question_id=self.question_id)}
        if user:
            endorsement_data = self.get_endorsement_data(user)
            public['endorse_type'] = endorsement_data['endorsement_type']
            public['mapx'] = str(endorsement_data['mapx'])
            public['mapy'] = str(endorsement_data['mapy'])
        else:
            public['endorse_type'] = 'notvoted'
            public['mapx'] = 'None'
            public['mapy'] = 'None'

        return public

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    blurb = db.Column(db.Text, nullable=False)
    abstract = db.Column(db.Text, nullable=False)
    generation_created = db.Column(db.Integer, default=1)
    created = db.Column(db.DateTime)
    source = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    geomedx = db.Column(db.Float)
    geomedy = db.Column(db.Float)
    # 1:M
    endorsements = db.relationship('Endorsement', backref="proposal",
                                   lazy='dynamic',
                                   cascade="all, delete-orphan")

    history = db.relationship('QuestionHistory',
                              backref=db.backref("proposal", lazy="joined"),
                              lazy='joined', cascade="all, delete-orphan")

    comments = db.relationship(
        'Comment',
        backref=db.backref('proposal'),
        primaryjoin="Comment.proposal_id == Proposal.id",
        lazy='dynamic')

    def __init__(self, author, question, title, blurb,
                 abstract='', source=0):
        '''
        .. function:: __init__(author, question, title, blurb
                [, abstract=None, source=0])

        Creates a Proposal object.

        :param author: author of the question
        :type author: User
        :param question: unique ID of the related question
        :type question: int
        :param title: question title
        :type title: string
        :param blurb: question content
        :type blurb: string
        :param abstract: question abstract
        :type abstract: string
        :param source: the id of its parent proposal if one exists, or 0
        :type source: int
        '''
        self.user_id = author.id
        self.question_id = question.id
        self.title = title
        self.blurb = blurb
        self.generation_created = question.generation
        self.created = datetime.datetime.utcnow()
        self.abstract = abstract
        self.question = question
        self.source = source

    def all_votes(self, generation=None):
        generation = generation or self.question.generation
        all_votes = dict()

        proposals = self.get_proposals_list(generation)
        generation_votes = dict()
        confused_count = 0
        oppose_count = 0
        for proposal in proposals:
            voters_by_type = proposal.voters_by_type(gen)
            # generation_votes.append({'proposal': proposal.id, 'votes': voters_by_type})
            generation_votes[proposal.id]= {'proposal': proposal.id, 'votes': voters_by_type}
            confused_count = confused_count + len(voters_by_type['confused'])
            oppose_count = oppose_count + len(voters_by_type['oppose'])
        # voting_map.append({'generation': gen, 'votes': generation_votes})
        voting_map[gen] = {'generation': gen, 
                           'proposals': generation_votes, 
                           'confused_count': confused_count, 
                           'oppose_count': oppose_count}
        return voting_map
    
    def get_endorser_count(self, generation=None):
        '''
        .. function:: get_endorser_count([generation=None])

        Returns the number of people who endorsed this proposal in the voting round
        during the selected generation of the question.

        :param generation: question generation.
        :type generation: int
        :rtype: int
        '''
        generation = generation or self.question.generation
        return self.endorsements.filter(and_(
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation,
            Endorsement.endorsement_type == 'endorse')
        ).count()
    
    def get_question_count(self, generation=None):
        '''
        .. function:: get_question_count([generation=None])

        Get all comments for a particular generation of the propsal.

        :param generation: proposal generation, defaults to current
        :type generation: int
        :rtype: list
        '''
        if generation:
            comments = self.comments.filter(Comment.generation == generation,
                                            Comment.comment_type == 'question').order_by(Comment.id).count()
        else:
            comments = self.comments.filter(Comment.comment_type == 'question').order_by(Comment.id).count()
        return comments

    def get_vote_count(self):
        '''
        .. function:: get_vote_count()

        Get the current vote count for the propsal.

        :rtype: integer
        '''
        return self.endorsements.filter(Endorsement.generation == self.question.generation).count()
    
    def get_comment_count(self, generation=None):
        '''
        .. function:: get_comment_count([generation=None])

        Get all comments for a particular generation of the propsal.

        :param generation: proposal generation, defaults to current
        :type generation: int
        :rtype: list
        '''
        if generation:
            comments = self.comments.filter(Comment.generation == generation,
                                            or_(Comment.comment_type == 'for',
                                                Comment.comment_type == 'against')).order_by(Comment.id).count()
        else:
            comments = self.comments.filter(or_(Comment.comment_type == 'for',
                                                Comment.comment_type == 'against')).order_by(Comment.id).count()
        return comments

    def get_comments(self, generation=None):
        '''
        .. function:: get_comments([generation=None])

        Get all comments for a particular generation of the propsal.

        :param generation: proposal generation, defaults to current
        :type generation: int
        :rtype: list
        '''
        if generation:
            app.logger.debug("get_comments: generation = %s", generation)
            comments = self.comments.filter(Comment.generation == generation).order_by(Comment.id).all()
        else:
            app.logger.debug("get_comments: fetching ALL comments")
            comments = self.comments.order_by(Comment.id).all()
            app.logger.debug("get_comments: ALL comments = %s", comments)
        return comments

    def publish(self):
        self.history.append(QuestionHistory(self))

    def update(self, user, title, blurb, abstract=None):
        '''
        .. function:: update(user, title, blurb[, abstract=None])

        Update the title and content of this proposal. Only available to the
        author during the question WRITING PHASE of the generation the
        proposal was first propsosed (created).

        :param user: user
        :type user: User object
        :param title: updated proposal title
        :type title: string
        :param blurb: updated proposal content
        :type blurb: string
        :param abstract: updated proposal abstract
        :type abstract: string or None
        :rtype: boolean
        '''
        if (user.id == self.user_id
                and self.question.phase == 'writing'
                and self.question.generation == self.generation_created):
            if (len(title) > 0 and len(blurb) > 0):
                self.title = title
                self.blurb = blurb
                self.abstract = abstract
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

    def endorse(self, endorser, endorsement_type="endorse", coords={'mapx': None, 'mapy': None}):
        '''
        .. function:: endorse(endorser, endorsement_type="endorse"[, comments=[]])

        Add a user's endorsement to this proposal.

        :param endorser: user
        :type endorser: User object
        :param endorsement_type: type of endorsement
        :type endorsement_type: string
        :param comments: list of comments to support
        :type comments: list
        '''
        if self.is_endorsed_by(endorser):
            self.update_endorsement(endorser, endorsement_type, coords)
        else:
            self.endorsements.append(Endorsement(endorser,
                                                 self,
                                                 endorsement_type,
                                                 coords))
        return self

    def calculate_geometric_median(self, generation=None): # WTF
        generation = generation or self.question.generation
        endorsements = self.endorsements.filter(
            Endorsement.generation == generation).all()
        data_points = []
        for endorsement in endorsements:
            coords = [endorsement.mapx, endorsement.mapy]
            data_points.append(coords)
        geometric_median = findGeometricMedian(data_points)
        self.geomedx = geometric_median[0]
        self.geomedy = geometric_median[1]
        db_session.commit()


    def update_endorsement(self, endorser, endorsement_type, coords={'mapx': None, 'mapy': None}):
        '''
        .. function:: update_endorsement(endorser, endorsement_type)

        Update a user's endorsement for this proposal.

        :param endorser: user endorsing the proposal
        :type endorser: User object
        :param endorsement_type: one of enbdorse, oppose or confused
        :type endorsement_type: string
        :rtype: boolean
        '''
        endorsement = self.endorsements.filter(and_(
            Endorsement.user_id == endorser.id,
            Endorsement.proposal_id == self.id)).first()
        if endorsement:
            endorsement.endorsement_type = endorsement_type
            endorsement.mapx =  coords['mapx']
            endorsement.mapy = coords['mapy']
            db_session.commit()
            return True
        else:
            return False

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

    def is_supported_by(self, user, generation=None):
        '''
        .. function:: is_endorsed_by(user[, generation=None])

        Check if the user has endorsed this proposal.
        Takes an optional generation value to check historic endorsements.

        :param user: user
        :param generation: question generation
        :type generation: int or None
        :rtype: boolean
        '''
        generation = generation or self.question.generation

        return self.endorsements.filter(and_(
            Endorsement.user_id == user.id,
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation,
            Endorsement.endorsement_type == 'endorse')
        ).count() == 1

    def is_endorsed_by(self, user, generation=None):
        '''
        .. function:: is_endorsed_by(user[, generation=None])

        Check if the user has endorsed this proposal.
        Takes an optional generation value to check historic endorsements.

        :param user: user
        :param generation: question generation
        :type generation: int or None
        :rtype: boolean
        '''
        generation = generation or self.question.generation

        return self.endorsements.filter(and_(
            Endorsement.user_id == user.id,
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation)
        ).count() == 1

    def get_endorsement_data(self, user, generation=None):
        '''
        .. function:: get_endorsement_data(user[, generation=None])

        Check if the user has endorsed this proposal.
        Takes an optional generation value to check historic endorsements.

        :param user: user
        :param generation: question generation
        :type generation: int or None
        :rtype: dict
        '''
        generation = generation or self.question.generation

        app.logger.debug('get_endorsement_data called with user %s', user.username)

        endorsement = self.endorsements.filter(and_(
            Endorsement.user_id == user.id,
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation)
        ).first()

        if not endorsement:
            return {
                'endorsement_type': 'notvoted',
                'mapx': None,
                'mapy': None
            }
        else:
            return {
                'endorsement_type': endorsement.endorsement_type,
                'mapx': endorsement.mapx,
                'mapy': endorsement.mapy
            }
    
    def get_endorsement_type(self, user, generation=None):
        '''
        .. function:: get_endorsement_type(user[, generation=None])

        Check if the user has endorsed this proposal.
        Takes an optional generation value to check historic endorsements.

        :param user: user
        :param generation: question generation
        :type generation: int or None
        :rtype: string
        '''
        generation = generation or self.question.generation

        app.logger.debug('get_endorsement_type called with user %s', user.username)

        endorsement = self.endorsements.filter(and_(
            Endorsement.user_id == user.id,
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation)
        ).first()

        if not endorsement:
            return 'notvoted'
        else:
            return endorsement.endorsement_type

    def endorsers_list(self, generation=None):
        '''
        .. function:: endorsers([generation=None])

        Returns a set of the current endorsers
            - Defaults to current generation

        :param generation: question generation
        :type generation: int or None
        :rtype: set
        '''
        generation = generation or self.question.generation
        current_endorsements = list()
        current_endorsements = self.endorsements.filter(and_(
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation,
            Endorsement.endorsement_type == 'endorse')
        ).all()
        endorsers = list()
        for e in current_endorsements:
            endorsers.append(e.endorser)
        endorsers.sort(key=lambda x: x.id, reverse=False)
        return endorsers
    
    def all_voters(self, generation=None):
        '''
        .. function:: endorsers([generation=None])

        Returns a set of the current endorsers
            - Defaults to current generation

        :param generation: question generation
        :type generation: int or None
        :rtype: set
        '''
        all_endorsements = list()
        
        if not generation:
            current_endorsements = self.endorsements.filter(
                Endorsement.proposal_id == self.id
            ).all()
        else:
            current_endorsements = self.endorsements.filter(and_(
                Endorsement.proposal_id == self.id,
                Endorsement.generation == generation)
            ).all()

        voters = set()
        for e in current_endorsements:
            voters.add(e.endorser)
        return voters
    
    def endorsers(self, generation=None):
        '''
        .. function:: endorsers([generation=None])

        Returns a set of the current endorsers
            - Defaults to current generation

        :param generation: question generation
        :type generation: int or None
        :rtype: set
        '''
        generation = generation or self.question.generation
        current_endorsements = list()
        current_endorsements = self.endorsements.filter(and_(
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation,
            Endorsement.endorsement_type == 'endorse')
        ).all()
        endorsers = set()
        for e in current_endorsements:
            endorsers.add(e.endorser)
        return endorsers

    def voters_by_type(self, return_sets=None, generation=None):
        '''
        .. function:: endorsers([generation=None])

        Returns a set of the current endorsers
            - Defaults to current generation

        :param generation: question generation
        :type generation: int or None
        :rtype: set
        '''
        generation = generation or self.question.generation
        return_sets = return_sets or False
        
        current_endorsements = list()
        current_endorsements = self.endorsements.filter(and_(
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation)
        ).all()

        endorse = []
        oppose = []
        confused = []
        for e in current_endorsements:
            if e.endorsement_type == 'endorse':
                endorse.append(e.endorser.id)
            elif e.endorsement_type == 'oppose':
                oppose.append(e.endorser.id)
            elif e.endorsement_type == 'confused':
                confused.append(e.endorser.id)

        endorsment_types = dict()

        if return_sets:
            endorsment_types['endorse'] = set(endorse)
            endorsment_types['oppose'] = set(oppose)
            endorsment_types['confused'] = set(confused)
        else:
            endorsment_types['endorse'] = endorse
            endorsment_types['oppose'] = oppose
            endorsment_types['confused'] = confused

        return endorsment_types

    def is_completely_understood(self, generation=None): # thu
        '''
        .. function:: endorsers([generation=None])

        Returns a set of the current endorsers
            - Defaults to current generation

        :param generation: question generation
        :type generation: int or None
        :rtype: set
        '''
        generation = generation or self.question.generation
        current_endorsements = self.endorsements.filter(and_(
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation,
            Endorsement.endorsement_type == 'confused')
        ).count()
        return current_endorsements == 0
    
    def get_endorser_id_by_type(self, endorsement_type=None, generation=None):
        '''
        .. function:: endorsers([generation=None])

        Returns a set of the current endorsers
            - Defaults to current generation

        :param generation: question generation
        :type generation: int or None
        :rtype: set
        '''
        endorsement_type = endorsement_type or 'endorse'
        generation = generation or self.question.generation
        current_endorsements = list()
        current_endorsements = self.endorsements.filter(and_(
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation,
            Endorsement.endorsement_type == endorsement_type)
        ).all()
        endorsers = set()
        for e in current_endorsements:
            endorsers.add(e.endorser.id)
        return endorsers
    
    def qualified_endorsers(self, generation=None):
        '''
        .. function:: endorsers([generation=None])

        Returns a set of the current endorsers
            - Defaults to current generation

        :param generation: question generation
        :type generation: int or None
        :rtype: set
        '''
        generation = generation or self.question.generation
        current_endorsements = list()
        current_endorsements = self.endorsements.filter(and_(
            Endorsement.proposal_id == self.id,
            Endorsement.generation == generation,
            or_(
                Endorsement.endorsement_type == 'endorse',
                Endorsement.endorsement_type == 'oppose'))
        ).all()
        endorsers = set()
        for e in current_endorsements:
            endorsers.add(e.endorser)
        return endorsers

    @staticmethod
    def intersection_of_qualfied_endorser_ids(proposal1, proposal2, generation):
        proposal1_qualified = proposal1.set_of_qualfied_endorser_ids(generation)
        proposal2_qualified = proposal2.set_of_qualfied_endorser_ids(generation)
        return proposal1_qualified & proposal2_qualified

    def set_of_qualfied_endorser_ids(self, generation=None):
        '''
        .. function:: set_of_endorser_ids([generation=None])

        Returns the set of user IDs who endorsed this proposal in
        this generation.

        :param generation: proposal generation
        :type generation: int or None
        :rtype: set of int
        '''
        generation = generation or self.question.generation
        endorsers = self.qualified_endorsers(generation)
        endorser_ids = set()
        for endorser in endorsers:
            endorser_ids.add(endorser.id)
        return endorser_ids

    def set_of_endorser_ids(self, generation=None):
        '''
        .. function:: set_of_endorser_ids([generation=None])

        Returns the set of user IDs who endorsed this proposal in
        this generation.

        :param generation: proposal generation
        :type generation: int or None
        :rtype: set of int
        '''
        generation = generation or self.question.generation
        endorsers = self.endorsers(generation)
        endorser_ids = set()
        for endorser in endorsers:
            endorser_ids.add(endorser.id)
        return endorser_ids

    @staticmethod
    def who_dominates(proposal1_voters, proposal2_voters, generation, algorithm):
        if algorithm == 2:
            # Use Algorithm 2
            qualified_voters = Proposal.\
                        intersection_of_qualfied_endorser_ids(proposal1_voters,
                                                              proposal2_voters,
                                                              generation)
            return Proposal.\
                who_dominates_who_qualified(proposal1_voters,
                                            proposal2_voters,
                                            qualified_voters)
        else:
            # Use Algorithm 1
            return Proposal.who_dominates_who(proposal1_voters,
                                              proposal2_voters)

    
    @staticmethod
    def who_dominates_who_qualified(proposal1_voters, proposal2_voters, qualified_voters): # newgraph
        '''
        .. function:: who_dominates_who_qualified(proposal1, proposal2)

        Takes 2 SETS of Qualified ENDORSER IDs representing who endorsed each proposal
        and calulates which proposal if any domiantes the other.
        Returns either the dominating set, or an db.Integer value of:

            - 0 if the sets of endorsers are different
            - -1 if the sets of endorsers are the same

        :param proposal1_voters: set of voters for proposal 1
        :type proposal1_voters: set of int
        :param proposal2_voters: set of voters for proposal 2
        :type proposal2_voters: set of int
        :rtype: interger or set of int
        '''
        # app.logger.debug("who_dominates_who_qualified called with voters %s and %s and qualified %s",
        #    proposal1_voters, proposal2_voters, qualified_voters)
        
        # Remove unqualified voters from each proposal.
        #   ie find intersection with qualified endorsers
        #   (those that understand both proposal A and proposal B) ---- look
        proposal1_qualified = proposal1_voters & qualified_voters
        # app.logger.debug("proposal1_qualified = %s", proposal1_qualified)
        proposal2_qualified = proposal2_voters & qualified_voters
        # app.logger.debug("proposal2_qualified = %s", proposal2_qualified)

        # If proposal1 and proposal2 are the same return -2
        if (proposal1_qualified == proposal2_qualified):
            return -2
        # If proposal1 is empty return proposal2
        elif (len(proposal1_qualified) == 0):
            return proposal2_voters
        # If proposal2 is empty return proposal1
        elif (len(proposal2_qualified) == 0):
            return proposal1_voters
        # Check if proposal1 is a propoer subset of proposal2
        elif (proposal1_qualified < proposal2_qualified):
            return proposal2_voters
        # Check if proposal2 is a proper subset of proposal1
        elif (proposal2_qualified < proposal1_qualified):
            return proposal1_voters
        # proposal1 and proposal2 are different return 0
        else:
            return 0


    @staticmethod
    def who_dominates_who(proposal1_voters, proposal2_voters):
        '''
        .. function:: who_dominates_who(proposal1, proposal2)

        Takes 2 SETS of ENDORSER IDs representing who endorsed each proposal
        and calulates which proposal if any domiantes the other.
        Returns either the dominating set, or an db.Integer value of:

            - 0 if the sets of endorsers are different
            - -1 if the sets of endorsers are the same

        :param proposal1_voters: set of voters for proposal 1
        :type proposal1_voters: set of int
        :param proposal2_voters: set of voters for proposal 2
        :type proposal2_voters: set of int
        :rtype: interger or set of int
        '''
        # If proposal1 and proposal2 are the same return -1
        if (proposal1_voters == proposal2_voters):
            return -1
        # If proposal1 is empty return proposal2
        elif (len(proposal1_voters) == 0):
            return proposal2_voters
        # If proposal2 is empty return proposal1
        elif (len(proposal2_voters) == 0):
            return proposal1_voters
        # Check if proposal1 is a propoer subset of proposal2
        elif (proposal1_voters < proposal2_voters):
            return proposal2_voters
        # Check if proposal2 is a proper subset of proposal1
        elif (proposal2_voters < proposal1_voters):
            return proposal1_voters
        # proposal1_voters and proposal2_voters are different return 0
        else:
            return 0


class Threshold(db.Model):
    '''
    Stores voting map thresholds
    '''

    __tablename__ = 'threshold'
    
    def get_public(self):
        '''
        .. function:: get_public()

        Return public propoerties as string values for REST responses.

        :rtype: dict
        '''
        return {'id': str(self.id),
                'question_id': str(self.question_id),
                'generation': str(self.generation),
                'mapx': str(self.threshold),
                'mapy': str(self.threshold)}

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    generation = db.Column(db.Integer)
    mapx = db.Column(db.Float)
    mapy = db.Column(db.Float)

    def __init__(self, question, coords={'mapx': 0.5, 'mapy': 0.5}):
        self.question_id = question.id
        self.generation = question.generation
        self.mapx = coords['mapx']
        self.mapy = coords['mapy']


class Endorsement(db.Model):
    '''
    Stores endorsement data
    '''

    __tablename__ = 'endorsement'

    def get_public(self):
        '''
        .. function:: get_public()

        Return public propoerties as string values for REST responses.

        :rtype: dict
        '''
        return {'id': str(self.id),
                'endorser_username': self.endorser.username,
                'endorser_email': self.endorser.email,
                'generation': str(self.generation),
                'question_id': str(self.question_id),
                'proposal_id': str(self.proposal_id),
                'endorsement_date': str(self.endorsement_date),
                'endorsement_type': endorsement_type,
                'mapx': mapx,
                'mapy': mapy}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    generation = db.Column(db.Integer, nullable=False)
    endorsement_date = db.Column(db.DateTime)
    endorsement_type = db.Column(db.Enum('endorse', 'oppose', 'confused', name="endorsement_type_enum"),
                                 default='endorse')
    mapx = db.Column(db.Float)
    mapy = db.Column(db.Float)

    def __init__(self, endorser, proposal,
                 endorsement_type='endorse', coords={'mapx': None, 'mapy': None}):
        self.user_id = endorser.id
        self.question_id = proposal.question_id
        self.proposal_id = proposal.id
        self.generation = proposal.question.generation
        self.endorsement_date = datetime.datetime.utcnow()
        self.endorsement_type = endorsement_type
        self.mapx = coords['mapx']
        self.mapy = coords['mapy']


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
