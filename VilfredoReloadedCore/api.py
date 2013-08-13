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
REST API
'''

from flask import request,\
    url_for, jsonify, make_response, abort
from . import app, models  # login_manager
from . database import db_session
# from flask.ext.login import current_user
from sqlalchemy import and_
# Authentication
from functools import wraps
from flask import Response

REST_API_VERSION = 'v1'
REST_URL_PREFIX = '/api/' + REST_API_VERSION
RESULTS_PER_PAGE = 2

MAX_LEN_EMAIL = 60
MAX_LEN_USERNAME = 50
MAX_LEN_PASSWORD = 60
MIN_LEN_PASSWORD = 6
MAX_LEN_ROOM = 20
MIN_LEN_ROOM = 2
MAX_LEN_PROPOSAL_TITLE = 100
MAX_LEN_PROPOSAL_ABSTRACT = 1000
MAX_LEN_PROPOSAL_BLURB = 1000
MAX_LEN_QUESTION_TITLE = 100
MAX_LEN_QUESTION_BLURB = 1000


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'You have to login to make this request', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        app.logger.debug("Request authorization = %s\n", request.authorization)
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def check_auth(username, password):
    '''
    .. function:: check_auth(username, password)

    Authenticates user.

    :param username: user name.
    :type username: String
    :param password: user name.
    :type password: String
    :rtype: Boolean
    '''
    user = models.User.query.filter_by(username=username).one()
    if user is None:
        return False
    else:
        return user.check_password(password)


def get_authenticated_user(request):
    '''
    .. function:: get_authenticated_user(request)

    Returns the authenticated user.

    :param request: HTTP request.
    :type request: Object
    :rtype: User or None
    '''
    if (request.authorization):
        return models.User.query.\
            filter_by(username=request.authorization.username).one()
    return None


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


#
# Get Users
#
@app.route('/api/v1/users', methods=['GET'])
@app.route('/api/v1/users/<int:user_id>', methods=['GET'])
def api_get_users(user_id=None):
    '''
    .. http:get:: /users/(int:user_id)

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      GET /users/42 HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 200 OK
      Content-Type: application/json

        {
           "total_items": 5,
           "items": "2",
           "objects":
           [
               {
                   "username": "john",
                   "url": "/users/1",
                   "registered": "2013-08-12 09:51:38.559222",
                   "id": "1",
                   "last_seen": "2013-08-12 09:51:38.559240"
               },
               {
                   "username": "susan",
                   "url": "/users/2",
                   "registered": "2013-08-12 09:51:38.576731",
                   "id": "2",
                   "last_seen": "2013-08-12 09:51:38.576745"
               }
           ],
           "page": "1",
           "pages": "2"
        }

    :param user_id: user id
    :type user_id: int
    :query page: page number. default is 1
    :statuscode 200: no error
    :statuscode 404: there's no user
    '''
    app.logger.debug("api_get_users called...\n")

    # Get authenticated user or None
    current_user = get_authenticated_user(request)

    if user_id is not None:
        user = models.User.query.get(int(user_id))
        if user is None:
            abort(404)

        results = user.get_public()

        if current_user and current_user.id == user.id:
            results['email'] = user.email

        return jsonify(object=results), 200

    else:
        page = int(request.args.get('page', 1))
        users = models.User.query.paginate(page,
                                           RESULTS_PER_PAGE,
                                           False)
        items = len(users.items)
        pages = users.pages
        total_items = users.total

        results = []
        for u in users.items:
            results.append(u.get_public())

        return jsonify(total_items=total_items, items=str(items),
                       page=str(page), pages=str(pages),
                       objects=results), 200


# Update User Details
@app.route('/api/v1/users/<int:user_id>', methods=['PATCH'])
@requires_auth
def api_update_user(user_id):
    '''
    .. http:patch:: /users/(int:user_id)

    Update a user's details'.

    **Example request**:

   .. sourcecode:: http

      PATCH /users/42 HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 200 OK
      Content-Type: application/json

        {
           "total_items": 5,
           "items": "2",
           "objects":
           [
               {
                   "username": "john",
                   "url": "/users/1",
                   "registered": "2013-08-12 09:51:38.559222",
                   "id": "1",
                   "last_seen": "2013-08-12 09:51:38.559240"
               },
               {
                   "username": "susan",
                   "url": "/users/2",
                   "registered": "2013-08-12 09:51:38.576731",
                   "id": "2",
                   "last_seen": "2013-08-12 09:51:38.576745"
               }
           ],
           "page": "1",
           "pages": "2"
        }

    :param user_id: user id
    :type user_id: int
    :query page: page number. default is 1
    :type page: int
    :statuscode 200: no error
    :statuscode 404: there's no user
    '''
    if user_id is None:
        abort(404)

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("api_update_user called by %s...\n", user.id)

    if int(user_id) != user.id:
        response = {'message': 'You are not authorized to edit this resource'}
        return jsonify(objects=response), 401

    if not request.json:
        app.logger.debug("Non json request received...\n")
        abort(400)

    elif 'new_username' in request.json and \
            (request.json['new_username'] == '' or
             len(request.json['new_username']) > MAX_LEN_USERNAME):
        app.logger.debug("1...\n")
        abort(400)

    elif 'new_email' in request.json and \
            (request.json['new_email'] == '' or
             request.json['new_email'] > MAX_LEN_EMAIL):
        app.logger.debug("2...\n")
        abort(400)

    elif 'new_password' in request.json and \
            (len(request.json['new_password']) < MIN_LEN_PASSWORD or
             len(request.json['new_password']) > MAX_LEN_PASSWORD):
        app.logger.debug("3...\n")
        abort(400)

    elif models.User.username_available(request.json['new_username'])\
            is not True:
        response = {'message': 'New Username not available'}
        return jsonify(objects=response), 400

    elif models.User.email_available(request.json['email']) is not True:
            response = {'message': 'New Email not available'}
            return jsonify(objects=response), 400

    user.username = request.json.get('new_username', user.username)
    user.email = request.json.get('new_email', user.email)

    if 'new_password' in request.json:
        user.set_password(request.json['new_password'])

    db_session.add(user)
    db_session.commit()
    response = {'url': url_for('api_get_users', user_id=user.id)}

    return jsonify(object=response), 201


#
# Create User
#
@app.route('/api/v1/users', methods=['POST'])
def api_create_user():
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

        {
          "object":
          {
            "url": "/users/1"
          }
        }

    :json username: username
    :type username: string
    :json email: email address
    :type email: string
    :json password: password
    :type password: string
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_create_user called...\n")

    app.logger.debug("Request %s...\n", request.json)

    if not request.json:
        app.logger.debug("Non json request received...\n")
        message = "Non json request received"
        return jsonify(message=message), 400

    elif not 'username' in request.json or request.json['username'] == '' \
            or len(request.json['username']) > MAX_LEN_USERNAME:
        message = "Username must be less than %s characters" % MAX_LEN_USERNAME
        return jsonify(message=message), 400

    elif not 'email' in request.json or request.json['email'] == '' \
            or len(request.json['email']) > MAX_LEN_EMAIL:
        message = "Email required and must be shorter than %s characters" %\
                  MAX_LEN_EMAIL
        return jsonify(message=message), 400

    elif not 'password' in request.json or request.json['password'] == '' or \
            len(request.json['password']) < MIN_LEN_PASSWORD or \
            len(request.json['password']) > MAX_LEN_PASSWORD:
        message = "Password must be between %s and %s characters" %\
            (MIN_LEN_PASSWORD, MAX_LEN_PASSWORD)
        return jsonify(message=message), 400

    elif models.User.username_available(request.json['username'])\
            is not True:
        message = "Username not available"
        return jsonify(message=message), 400

    elif models.User.email_available(request.json['email']) is not True:
        message = "Email not available"
        return jsonify(message=message), 400

    user = models.User(request.json['username'],
                       request.json['email'],
                       request.json['password'])
    db_session.add(user)
    db_session.commit()
    response = {'url': url_for('api_get_users', user_id=user.id)}

    return jsonify(object=response), 201


#
# Get Questions
#
@app.route('/api/v1/questions', methods=['GET'])
@app.route('/api/v1/questions/<int:question_id>', methods=['GET'])
def api_get_questions(question_id=None):
    '''
    .. http:get:: /questions/(int:question_id)

    A question or list of questions.

    **Example request**:

   .. sourcecode:: http

      GET /questions/42 HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 200 OK
      Content-Type: application/json

        {
          "total_items": "3",
          "items": "2",
          "objects": [
            {
              "last_move_on": "2013-08-12 09:51:38.632780",
              "created": "2013-08-12 09:51:38.632763",
              "title": "My question",
              "minimum_time": "0",
              "maximum_time": "604800",
              "id": 1,
              "blurb": "My blurb"
            },
            {
              "last_move_on": "2013-08-12 09:51:38.665584",
              "created": "2013-08-12 09:51:38.665570",
              "title": "Too Many Chefs",
              "minimum_time": "0",
              "maximum_time": "604800",
              "id": 3,
              "blurb": "How can they avoid spoiling the broth?"
            }
          ],
          "page": "1",
          "pages": "1"
        }

    :param user_id: user id
    :query page: page number. default is 1
    :statuscode 200: no error
    :statuscode 404: there's no user
    '''
    app.logger.debug("api_get_questions called...\n")
    if question_id is not None:
        question = models.Question.query.get(int(question_id))
        if question is None:
            abort(404)

        results = [question.get_public()]
        return jsonify(object=results), 200

    else:
        page = int(request.args.get('page', 1))

        room = request.args.get('room', None)

        query = models.Question.query
        if not room is None:
            query = query.filter_by(room=room)

        questions = query.paginate(page,
                                   RESULTS_PER_PAGE,
                                   False)

        items = len(questions.items)
        pages = questions.pages
        total_items = questions.total

        results = []
        for q in questions.items:
            results.append(q.get_public())

        return jsonify(total_items=total_items, items=str(items),
                       page=str(page), pages=str(pages),
                       objects=results), 200


#
# Create Question
#
@app.route('/api/v1/questions', methods=['POST'])
@requires_auth
def api_create_question():
    '''
    .. http:post:: /questions

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /questions HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/questions/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_create_question called...\n")

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if not request.json:
        app.logger.debug("Non json request received...\n")
        abort(400)

    if not 'title' in request.json or request.json['title'] == ''\
            or len(request.json['title']) > MAX_LEN_QUESTION_TITLE:
        abort(400)

    elif not 'blurb' in request.json or request.json['blurb'] == ''\
            or len(request.json['blurb']) > MAX_LEN_QUESTION_BLURB:
        abort(400)

    elif 'room' in request.json and\
        (request.json['room'] == ''
         or len(request.json['room']) > MAX_LEN_ROOM
         or len(request.json['room']) < MIN_LEN_ROOM):
        abort(400)

    # Set required parameters
    title = request.json.get('title')
    blurb = request.json.get('blurb')
    # Set optional parameters
    room = request.json.get('room', None)
    minimum_time = request.json.get('minimum_time', 86400)
    maximum_time = request.json.get('maximum_time', 604800)

    question = models.Question(user,
                               title,
                               blurb,
                               minimum_time,
                               maximum_time,
                               room)
    db_session.add(question)
    db_session.commit()

    response = {'url': url_for('api_get_questions', question_id=question.id)}
    return jsonify(object=response), 201


@app.route('/api/v1/questions/<int:question_id>/subscribers', methods=['GET'])
def api_question_subscribers(question_id=None):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_question_subscribers called with %s...\n",
                     question_id)

    if question_id is None:
        app.logger.debug("ERROR: question_id is None!\n")
        abort(404)

    question = models.Question.query.get(int(question_id))

    if question is None:
        app.logger.debug("ERROR: Question %s Not Found!\n", question_id)
        abort(404)

    page = int(request.args.get('page', 1))
    subscriptions = question.subscriber_update.\
        paginate(page, RESULTS_PER_PAGE, False)
    items = len(subscriptions.items)
    pages = subscriptions.pages

    results = []
    for s in subscriptions:
        results.append(s.get_public())

    return jsonify(question_id=str(question.id),
                   items=(items), page=str(page), pages=str(pages),
                   num_items=str(subscriptions.total), objects=results), 200


# Get question proposals (Get Proposals)
@app.route('/api/v1/questions/<int:question_id>/proposals', methods=['GET'])
@app.route('/api/v1/questions/<int:question_id>/proposals/<int:proposal_id>',
           methods=['GET'])
def api_get_question_proposals(question_id=None, proposal_id=None):
    '''
    .. http:get:: /questions/(int:question_id)/proposals/(int:proposal_id)

    A proposal or list of proposals.

    **Example request**:

   .. sourcecode:: http

      GET /questions/22/proposals HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 200 OK
      Content-Type: application/json

    :param question_id: user ID
    :param proposal_id: proposal ID
    :query generation: question generation. default is current
    :query page: page number. default is 1
    :statuscode 200: no error
    :statuscode 404: there's no proposal
    '''
    app.logger.debug("api_get_question_proposals called...\n")

    if question_id is None:
        app.logger.debug("ERROR: question_id is None!\n")
        abort(404)

    question = models.Question.query.get(int(question_id))

    if question is None:
        app.logger.debug("ERROR: Question %s Not Found!\n", question_id)
        abort(404)

    if not proposal_id is None:
        proposal_id = int(proposal_id)
        proposal = question.proposals.filter_by(id=proposal_id).one()
        if proposal is None:
            abort(404)

        results = [proposal.get_public()]
        return jsonify(object=results), 200

    else:
        generation = int(request.args.get('generation', question.generation))
        page = int(request.args.get('page', 1))

        proposals = models.Proposal.query.join(models.QuestionHistory).\
            filter(models.QuestionHistory.question_id == question.id).\
            filter(models.QuestionHistory.generation == generation).\
            paginate(page, RESULTS_PER_PAGE, False)

        items = len(proposals.items)
        pages = proposals.pages
        total_items = proposals.total

        results = []
        for p in proposals.items:
            results.append(p.get_public())

        return jsonify(total_items=str(total_items), items=str(items),
                       page=str(page), pages=str(pages),
                       objects=results), 200


# Create Endorsement
#
# @app.route('/api/v1/proposals/<int:proposal_id>/endorsements',
#   methods=['POST'])
@app.route(
    '/api/v1/questions/<int:question_id>/proposals/' +
    '<int:proposal_id>/endorsements',
    methods=['POST'])
@requires_auth
def api_add_proposal_endorsement(question_id, proposal_id):
    '''
    .. http:post:: /users

        A user or list of users.

        **Example request**:

        .. sourcecode:: http

            POST /users HTTP/1.1
            Host: example.com
            Accept: application/json

        **Example response**:

        .. sourcecode:: http

            Status Code: 201 OK
            Content-Type: application/json

            {
                 "message": "Endorsement added"
            }

        :json username: username
        :json email: email address
        :json password: password
        :statuscode 201: no error
        :statuscode 400: bad request
    '''
    app.logger.debug("api_add_proposal_endorsement called...\n")

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if question_id is None or proposal_id is None:
        abort(404)

    question = models.Question.query.get(int(question_id))
    if question is None:
        abort(400)

    elif question.phase != 'voting':
        message = {"message": "The question is not in the voting phase"}
        return jsonify(message), 403

    proposal = models.Proposal.query.get(int(proposal_id))
    if proposal is None:
        abort(400)

    if proposal.is_endorsed_by(user):
        message = {"message": "User has already endorsed this proposal"}
        return jsonify(message), 400

    proposal.endorse(user)
    db_session.commit()

    return jsonify(message="Endorsement added"), 201


# Remove Endorsement
#
@app.route('/api/v1/questions/<int:question_id>/proposals/' +
           '<int:proposal_id>/endorsements',
           methods=['DELETE'])
@requires_auth
def api_remove_proposal_endorsement(question_id, proposal_id):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_remove_proposal_endorsement called...\n")

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if question_id is None or proposal_id is None:
        abort(404)

    question = models.Question.query.get(int(question_id))
    if question is None:
        abort(400)
    elif question.phase != 'voting':
        message = {"message": "The question is not in the voting phase"}
        return jsonify(message), 403

    proposal = models.Proposal.query.get(int(proposal_id))
    if proposal is None:
        abort(400)

    if not proposal.is_endorsed_by(user):
        message = {"message": "User has not yet endorsed this proposal"}
        return jsonify(message), 400

    proposal.remove_endorsement(user)
    db_session.commit()

    return jsonify(message="Endorsement removed"), 200


#
# Create proposal
#
@app.route('/api/v1/questions/<int:question_id>/proposals', methods=['POST'])
@requires_auth
def api_create_proposal(question_id):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_create_proposal called...\n")

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if question_id is None:
        abort(400)

    question = models.Question.query.get(int(question_id))
    if question is None:
        abort(400)

    if not request.json:
        app.logger.debug("Non json request received...\n")
        abort(400)

    if not 'title' in request.json or request.json['title'] == ''\
            or len(request.json['title']) > MAX_LEN_PROPOSAL_TITLE:
        abort(400)

    elif not 'blurb' in request.json or request.json['blurb'] == ''\
            or len(request.json['blurb']) > MAX_LEN_PROPOSAL_BLURB:
        abort(400)

    elif 'abstract' in request.json and \
            (request.json['abstract'] == ''
             or len(request.json['abstract']) > MAX_LEN_PROPOSAL_ABSTRACT):
        abort(400)

    app.logger.debug("1...\n")

    title = request.json.get('title')
    blurb = request.json.get('blurb')
    abstract = request.json.get('abstract', None)

    proposal = models.Proposal(user, question, title, blurb, abstract)
    db_session.add(proposal)
    db_session.commit()

    response = {'url': url_for('api_get_question_proposals',
                question_id=question_id, proposal_id=proposal.id)}
    return jsonify(object=response), 201


# Delete proposal
#
@app.route('/api/v1/questions/<int:question_id>/proposals/<int:proposal_id>',
           methods=['DELETE'])
@requires_auth
def api_delete_proposal(question_id, proposal_id):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_delete_proposal called...\n")

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if question_id is None or proposal_id is None:
        abort(404)

    proposal = models.Proposal.query.get(int(proposal_id))
    if proposal is None:
        abort(404)

    if user.id != proposal.user_id:
        message = {"message": "You are not authorized to delete this proposal"}
        return jsonify(message), 403

    if proposal.question.phase != 'writing'\
            or proposal.question.generation != proposal.generation_created:
        message = {"message": "This proposal may no longer be deleted"}
        return jsonify(message), 403

    user.delete_proposal(proposal)
    db_session.commit()
    return jsonify(message="Proposal deleted"), 200


# Delete Question
#
@app.route('/api/v1/questions/<int:question_id>', methods=['DELETE'])
@requires_auth
def api_delete_question(question_id):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

        {
          "message": "Question deleted"
        }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_delete_question called for question %s...\n",
                     question_id)

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if 'question_id' is None:
        abort(404)

    question = models.Question.query.get(int(question_id))
    if question is None:
        abort(404)

    # Cannot delete a question if not author
    if user.id != question.user_id:
        message = {"message":
                   "You are not authorized to delete this question"}
        return jsonify(message), 403

    # Cannot delete a question which has proposals
    if question.proposals.count() > 0:
        message = {"message":
                   "This question has proposals and may no longer be deleted"}
        return jsonify(message), 403

    db_session.delete(question)
    db_session.commit()
    return jsonify(message="Question deleted"), 200


# Update Question
#
@app.route('/api/v1/questions/<int:question_id>', methods=['PATCH'])
@requires_auth
def api_edit_question(question_id):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_edit_question called...\n")

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if 'question_id' is None:
        abort(404)

    question = models.Question.query.get(int(question_id))
    if question is None:
        abort(404)

    user_id = user.id

    # Cannot edit a question if not author
    if user_id != question.user_id:
        message = {"message": "You are not authorized to edit this question"}
        return jsonify(message), 403

    if 'move_on' in request.json:
        if not question.minimum_time_passed():
            app.logger.debug("Question cannot be moved on " +
                             "until minimum time has passed")
            message = {"message": "Question cannot be moved on " +
                                  "until minimum time has passed"}
            return jsonify(message), 405

        phase = question.author_move_on(user_id)
        db_session.commit()

        if not phase:
            return 500
        else:
            message = {"new_phase": phase}
            return jsonify(message), 200

    # Cannot edit a question which has proposals
    if question.propsals.count() > 0:
        message = {"message":
                   "This question has proposals and may no longer be edited"}
        return jsonify(message), 405

    if not 'title' in request.json or request.json['title'] == ''\
            or len(request.json['title']) > MAX_LEN_QUESTION_TITLE:
        abort(400)

    elif not 'blurb' in request.json or request.json['blurb'] == ''\
            or len(request.json['blurb']) > MAX_LEN_QUESTION_BLURB:
        abort(400)

    question.title = request.json.get('title')
    question.blurb = request.json.get('blurb')

    db_session.add(question)
    db_session.commit()
    return jsonify(message="Question updated"), 200


# Edit proposal
#
@app.route('/api/v1/questions/<int:question_id>/proposals/<int:proposal_id>',
           methods=['PATCH'])
@requires_auth
def api_edit_proposal(question_id, proposal_id):
    '''
    .. http:patch:: questions/int:question_id/proposals/int:proposal_id

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      PATCH questions/22/proposals/14 HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

        {
          "message": "Proposal updated"
        }

    :param question_id: question id
    :param proposal_id: proposal id
    :json title: title
    :json blurb: question content
    :json abstract: optional abstract
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_edit_proposal called...\n")

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if 'question_id' is None or 'proposal_id' is None:
        abort(404)

    if not 'title' in request.json or request.json['title'] == '' \
            or len(request.json['blurb']) > MAX_LEN_PROPOSAL_TITLE:
        abort(400)

    elif not 'blurb' in request.json or request.json['blurb'] == '' \
            or len(request.json['blurb']) > MAX_LEN_PROPOSAL_BLURB:
        abort(400)

    elif 'abstract' in request.json and \
            (request.json['abstract'] == ''
             or len(request.json['abstract']) > MAX_LEN_PROPOSAL_ABSTRACT):
        abort(400)

    title = request.json.get('title')
    blurb = request.json.get('blurb')
    abstract = request.json.get('abstract', None)

    proposal = models.Proposal.query.get(int(proposal_id))
    if proposal is None:
        abort(404)

    if user.id != proposal.user_id:
        message = {"message": "You are not authorized to edit this proposal"}
        return jsonify(message), 403

    if proposal.question.phase != 'writing'\
            or proposal.question.generation != proposal.generation_created:
        message = {"message": "This proposal may no longer be edited"}
        return jsonify(message), 403

    if proposal.update(user, title, blurb, abstract):
        db_session.commit()
        message = {"message":
                   "Proposal updated"}
        return jsonify(message), 200
    else:
        message = {"message": "There was an error updating this proposal"}
        return jsonify(message), 400


# Get Proposal Endorsers
@app.route('/api/v1/questions/<int:question_id>/proposals/' +
           '<int:proposal_id>/endorsers',
           methods=['GET'])
def api_get_question_proposal_endorsers(question_id=None, proposal_id=None):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :param question_id: question id
    :param proposal_id: proposal id
    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_get_question_proposal_endorsers called...\n")

    if question_id is None or proposal_id is None:
        app.logger.debug("ERROR: question_id or proposal_id is None!\n")
        abort(404)

    question = models.Question.query.get(int(question_id))
    if question is None:
        abort(404)

    proposal = models.Proposal.query.get(int(proposal_id))
    if proposal is None:
        abort(404)

    generation = int(request.args.get('generation', question.generation))
    endorsers = proposal.endorsers(generation=generation)

    results = []
    for e in endorsers:
        results.append(e.get_public())

    return jsonify(question_id=str(question.id),
                   query_generation=str(generation),
                   current_generation=str(question.generation),
                   num_items=str(len(endorsers)), objects=results), 200


#
# Get Pareto Front
#
@app.route('/api/v1/questions/<int:question_id>/pareto', methods=['GET'])
def api_question_pareto(question_id=None):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :param question_id: question id
    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_question_pareto called with %s...\n", question_id)

    if question_id is None:
        app.logger.debug("ERROR: question_id is None!\n")
        abort(404)

    question = models.Question.query.get(int(question_id))

    if question is None:
        app.logger.debug("ERROR: Question %s Not Found!\n", question_id)
        abort(404)

    generation = int(request.args.get('generation', question.generation))
    pareto = question.calculate_pareto_front(generation=generation)

    results = []
    for p in pareto:
        results.append(p.get_public())

    return jsonify(question_id=str(question.id),
                   query_generation=str(generation),
                   current_generation=str(question.generation),
                   num_items=str(len(pareto)), objects=results), 200


@app.route('/api/v1/questions/<int:question_id>/key_players', methods=['GET'])
def api_question_key_players(question_id=None):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :param question_id: question id
    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_question_key_players called with %s...\n",
                     question_id)

    if question_id is None:
        app.logger.debug("ERROR: question_id is None!\n")
        abort(404)

    question = models.Question.query.get(int(question_id))

    if question is None:
        app.logger.debug("ERROR: Question %s Not Found!\n", question_id)
        abort(404)

    generation = int(request.args.get('generation', question.generation))
    key_players = question.calculate_key_players(generation=generation)

    app.logger.debug("Key Players: %s", key_players)

    results = []
    for (endorser, vote_for) in key_players.iteritems():
        proposals = []
        for proposal in vote_for:
            proposals.append(url_for('api_get_question_proposals',
                                     question_id=question.id,
                                     proposal_id=proposal.id))
        kp = {endorser: proposals}
        results.append(kp)

    return jsonify(question_id=str(question.id),
                   query_generation=str(generation),
                   current_generation=str(question.generation),
                   num_items=str(len(key_players)), objects=results), 200


@app.route('/api/v1/questions/<int:question_id>/endorser_effects',
           methods=['GET'])
def api_question_endorser_effects(question_id=None):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_question_endorser_effects called with %s...\n",
                     question_id)

    if question_id is None:
        app.logger.debug("ERROR: question_id is None!\n")
        abort(404)

    question = models.Question.query.get(int(question_id))

    if question is None:
        app.logger.debug("ERROR: Question %s Not Found!\n", question_id)
        abort(404)

    generation = int(request.args.get('generation', question.generation))
    endorser_effects = question.\
        calculate_endorser_effects(generation=generation)

    app.logger.debug("Endorser Effects==> %s", endorser_effects)

    results = []
    for (endorser, effects) in endorser_effects.iteritems():
        endorser_effects = dict()

        if not effects is None:
            PF_excluding_pulbic = replaceWithPublic(effects['PF_excluding'])
            PF_plus_public = replaceWithPublic(effects['PF_plus'])
            PF_minus_public = replaceWithPublic(effects['PF_minus'])

            endorser_effects = {
                'PF_excluding': PF_excluding_pulbic,
                'PF_plus': PF_plus_public,
                'PF_minus': PF_minus_public}
        else:
            endorser_effects = {}

        results.append({endorser.id: endorser_effects})

    return jsonify(question_id=str(question.id),
                   query_generation=str(generation),
                   current_generation=str(question.generation),
                   num_items=str(len(results)), objects=results), 200


def replaceWithPublic(collection):
    public = []
    for c in collection:
        public.append(c.get_public())
    return public


# http://[hostname]/api/v1.0/questions/47/graph?generation=2&graphtype=pareto
@app.route('/api/v1/questions/<int:question_id>/graph', methods=['GET'])
def api_question_graph(question_id):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_question_votingmap called...\n")

    if question_id is None:
        app.logger.debug("ERROR: question_id is None!\n")
        abort(404)

    question = models.Question.query.get(int(question_id))

    if question is None:
        app.logger.debug("ERROR: Question %s Not Found!\n", question_id)
        abort(404)

    generation = int(request.args.get('generation', question.generation))
    map_type = request.args.get('map_type', 'votes')

    app.logger.debug("Call get_voting_graph()...")
    graph_url = question.get_voting_graph(generation=generation,
                                          map_type=map_type)

    # results = []
    # results.append({'url': graph_url})

    return jsonify(question_id=str(question.id),
                   query_generation=str(generation),
                   current_generation=str(question.generation),
                   url=graph_url), 200


@app.route('/api/v1/questions/<int:question_id>/proposal_relations',
           methods=['GET'])
def api_question_proposal_relations(question_id=None):
    '''
    .. http:post:: questions/(int:question_id)/proposal_relations

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      GET questions/42/proposal_relations HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
          "query_generation": "1",
          "current_generation": "1",
          "objects": [
            {
              "3": {
                "dominating": [
                  {
                    "question_url": "/api/v1/questions/1",
                    "author_url": "/api/v1/users/3",
                    "title": "Bills First Proposal",
                    "url": "/api/v1/questions/1/proposals/1",
                    "abstract": null,
                    "created": "2013-08-13 10:42:55.625328",
                    "id": "1",
                    "blurb": "Bills blurb of varying interest",
                    "generation_created": "1"
                  }
                ],
                "dominated": []
              }
            },
            {
              "2": {
                "dominating": [],
                "dominated": []
              }
            },
            {
              "1": {
                "dominating": [],
                "dominated": [
                  {
                    "question_url": "/api/v1/questions/1",
                    "author_url": "/api/v1/users/2",
                    "title": "Susans Only Proposal",
                    "url": "/api/v1/questions/1/proposals/3",
                    "abstract": "Blah blah blah",
                    "created": "2013-08-13 10:42:55.664450",
                    "id": "3",
                    "blurb": "My blub is cool",
                    "generation_created": "1"
                  }
                ]
              }
            },
            {
              "4": {
                "dominating": [],
                "dominated": []
              }
            }
          ],
          "num_items": "4",
          "question_id": "1"
       }

    :param question_id: question id
    :type question_id: int
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_question_proposal_relations called with %s...\n",
                     question_id)

    if question_id is None:
        app.logger.debug("ERROR: question_id is None!\n")
        abort(404)

    question = models.Question.query.get(int(question_id))

    if question is None:
        app.logger.debug("ERROR: Question %s Not Found!\n", question_id)
        abort(404)

    generation = int(request.args.get('generation', question.generation))
    proposal_relations =\
        question.calculate_proposal_relations(generation=generation)

    app.logger.debug("Proposal Relations==> %s", proposal_relations)

    results = []
    for (proposal, relations) in proposal_relations.iteritems():
        dominated_public = replaceWithPublic(relations['dominated'])
        dominating_public = replaceWithPublic(relations['dominating'])

        prop_relations = {
            'dominated': dominated_public,
            'dominating': dominating_public}

        results.append({proposal.id: prop_relations})

    return jsonify(
        question_id=str(question.id),
        query_generation=str(generation),
        current_generation=str(question.generation),
        num_items=str(len(proposal_relations)), objects=results), 200


# Get Invitations
@app.route('/api/v1/questions/<int:question_id>/invitations',
           methods=['GET'])
def api_get_invitations(question_id):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_get_invitations called...\n")

    if question_id is None:
        abort(404)

    if not request.json:
        abort(400)

    question = models.Question.query.get(int(question_id))
    if question is None:
        abort(400)

    page = int(request.args.get('page', 1))

    invites = question.author.invitations.filter_by(question_id=question_id).\
        paginate(page, RESULTS_PER_PAGE, False)

    items = len(invites.items)
    pages = invites.pages
    total_items = invites.total

    results = []
    for i in invites.items:
        results.append(i.get_public())

    return jsonify(total_items=str(total_items), items=str(items),
                   page=str(page), pages=str(pages),
                   objects=results), 200


# Create Invitation
@app.route('/api/v1/questions/<int:question_id>/invitations',
           methods=['POST'])
@requires_auth
def api_create_invitation(question_id):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_create_invitation called...\n")

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if question_id is None:
        abort(404)

    if not request.json:
        abort(400)

    if not 'invite_user_ids' in request.json:
        abort(400)

    invite_user_ids = request.json['invite_user_ids']

    for id in invite_user_ids:
        try:
            id = int(id)
        except ValueError:
            app.logger.debug(
                "Param invite_user_ids contains non integer values!\n")
            abort(400)

    app.logger.debug("invite_user_ids = %s\n", invite_user_ids)

    question = models.Question.query.get(int(question_id))
    if question is None:
        abort(400)

    app.logger.debug("calling invite_all with users %s\n", invite_user_ids)
    if user.invite_all(invite_user_ids, question):
        app.logger.debug("invites created\n")
        db_session.commit()
        return jsonify(message="Invites sent"), 201
    else:
        abort(500)


# Get subscriptions
#
@app.route('/api/v1/users/<int:user_id>/subscriptions', methods=['GET'])
@app.route('/api/v1/users/<int:user_id>/subscriptions/<int:question_id>',
           methods=['GET'])
def api_get_user_subscriptions(user_id, question_id=None):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

        {
          "total_items": 3,
          "items": 2,
          "objects": [
            {
              "url": "/users/1/subscriptions/1",
              "how": "asap",
              "last_update": "None",
              "question_id": "1"
            },
            {
              "url": "/users/1/subscriptions/2",
              "how": "asap",
              "last_update": "None",
              "question_id": "2"
            }
          ],
          "page": "1",
          "pages": "2"
        }

    :param user_id: user id
    :type user_id: int
    :param question_id: question id
    :type question_id: int
    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_get_user_subscriptions called...\n")

    if user_id is None:
        abort(404)

    user = models.User.query.get(int(user_id))

    if question_id is not None:

        subscribed_question = user.subscribed_questions.\
            filter(models.Update.question_id == int(question_id)).one()

        if subscribed_question is None:
            abort(404)

        app.logger.debug("Subscribed question ID %s\n",
                         subscribed_question.question_id)
        '''
        subscriptions = [{'question_id': subscribed_question.question_id,
                          'how': subscribed_question.how,
                          'last_update': str(subscribed_question.last_update)}]
        '''
        results = [subscribed_question.get_public()]
        return jsonify(object=results), 200

    else:
        page = int(request.args.get('page', 1))
        subscribed_questions = user.subscribed_questions.\
            paginate(page, RESULTS_PER_PAGE, False)
        items = len(subscribed_questions.items)
        pages = subscribed_questions.pages
        total_items = subscribed_questions.total

        results = []
        for s in subscribed_questions.items:
            results.append(s.get_public())

        return jsonify(total_items=total_items, items=(items),
                       page=str(page), pages=str(pages),
                       objects=results), 200


#
# Create Subscription
#
@app.route('/api/v1/users/<int:user_id>/subscriptions', methods=['POST'])
@requires_auth
def api_add_user_subscriptions(user_id):
    '''
    .. http:post:: /users

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      POST /users HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :json username: username
    :json email: email address
    :json password: password
    :statuscode 201: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_add_user_subscriptions called...\n")

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if not request.json:
        abort(400)

    if not 'how' in request.json\
            or not request.json['how'] in ['daily', 'weekly', 'asap']:
        abort(400)

    if not 'question_id' in request.json:
        abort(400)

    question_id = int(request.json['question_id'])
    how = request.json['how']

    if user.subscribed_questions.filter(
            models.Update.question_id == question_id).count() == 1:
        abort(400)

    question = models.Question.query.get(question_id)
    if question is None:
        abort(400)

    user.subscribe_to(question, how)
    db_session.add(user)
    db_session.commit()

    return jsonify({'url': url_for('api_get_user_subscriptions',
                                   user_id=user_id,
                                   question_id=question_id)}), 201


# Delete subscription
#
# @app.route('/api/v1/subscriptions/<int:question_id>',
@app.route('/api/v1/users/<int:user_id>/subscriptions/<int:question_id>',
           methods=['DELETE'])
@requires_auth
def api_delete_user_subscriptions(user_id, question_id):
    '''
    .. http:delete:: /users/(int:user_id)/subscriptions/(int:question_id)

    A user or list of users.

    **Example request**:

   .. sourcecode:: http

      DELETE users/56/subscriptions/44 HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
        "message": "Subscription Deleted"
      }

    :param user_id: user id
    :param question_id: question id
    :statuscode 200: no error
    :statuscode 400: bad request
    '''
    app.logger.debug("api_delete_user_subscriptions called...\n")

    user = get_authenticated_user(request)

    if user is None:
        abort(404)

    if user_id is None:
        abort(400)

    if user.id != user_id:
        abort(401)

    if question_id is None:
        abort(404)

    app.logger.debug("Authenticated User = %s\n", user.id)

    subscription = user.subscribed_questions.filter(and_(
        models.Update.question_id == int(question_id),
        models.Update.user_id == user.id)).first()

    if subscription is not None:
        user.subscribed_questions.remove(subscription)
    db_session.add(user)
    db_session.commit()
    return jsonify(message="Subscription deleted"), 200


#
# Update subscription
#
@app.route('/api/v1/users/<int:user_id>/subscriptions/<int:question_id>',
           methods=['PATCH'])
@requires_auth
def api_update_user_subscriptions(user_id, question_id):
    '''
    .. http:patch:: /users/(int:user_id)/subscriptions/(int:question_id)

    Update a user's question subscription'.

    **Example request**:

   .. sourcecode:: http

      PATCH users/56/subscriptions/44 HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Status Code: 201 OK
      Content-Type: application/json

      {
         "url": "/users/10"
      }

    :param user_id: user id
    :type user_id: int
    :param question_id: question id
    :type question_id: int
    :json how: one of daily, weekly, or asap
    :type how: string
    :statuscode 201: no error
    :statuscode 400: bad request
    :statuscode 401: unauthorized
    '''
    app.logger.debug("api_update_user_subscriptions called...\n")

    user = get_authenticated_user(request)
    if not user:
        abort(401)

    app.logger.debug("Authenticated User = %s\n", user.id)

    if user_id is None:
        abort(400)

    if user.id != user_id:
        abort(401)

    if question_id is None:
        abort(400)

    if not request.json or not 'how' in request.json \
            or not request.json['how'] in ['daily', 'weekly', 'asap']:
        msg_txt = "You must supply the parameter 'how' " +\
                  "set to one of the desired" +\
                  "update methods: 'daily', 'weekly', 'asap'"
        message = [{"message": msg_txt}]
        return jsonify(objects=message), 400

    subscription = user.subscribed_questions.\
        filter(models.Update.question_id == int(question_id)).first()

    if subscription is None:
        abort(404)

    subscription.how = request.json['how']
    # db_session.add(user)
    db_session.commit()

    subscription = [{'question_id': subscription.question_id,
                    'how': subscription.how,
                    'last_update': str(subscription.last_update)}]

    return jsonify(objects=subscription), 200
