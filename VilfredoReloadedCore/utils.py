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
from VilfredoReloadedCore import app
from sqlalchemy import and_, or_, not_, event, distinct, func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from database import db_session, db

def make_site_link(url):
    return app.config['PROTOCOL']+app.config['SITE_DOMAIN']+url

def get_user_permissions(question_id, user_id):
    '''
    .. function:: get_user_permissions()

    Get user's permissions to access this question,
    granted either through being the author or through having been invited
    to participate.

    :rtype: Integer
    '''
    stmt = text('SELECT permissions FROM invite WHERE invite.question_id = :qid AND invite.receiver_id = :user_id')
    result = db_session.execute(stmt, {"user_id": user_id, "qid": question_id})
    perm = result.scalar()
    result.close()
    return perm


def alter_question_permissions(question_ids, old_permission, new_permission):
    '''
    .. function:: alter_question_permissions(question_ids, old_permission, new_permission)

    Updates permissions of all paticipants with permissions == old_permission to new_permission.

    :param question_ids: List of question IDs
    :type question_ids: List
    :param old_permission: current permissions
    :type old_permission: int
    :param new_permission: new permissions
    :type new_permission: int
    :rtype: Boolean
    '''         
    try:
        if type(question_ids) is list and \
                all(isinstance(item, int) for item in question_ids) and \
                type(old_permission) is int and type(new_permission) is int:
            stmt = text('UPDATE invite SET invite.permissions = :new_perm WHERE invite.question_id IN :qid_array AND invite.permissions = :old_perm')
            db_session.execute(stmt, {"new_perm": new_permission, "qid_array": question_ids, "old_perm": old_permission})
            return True
        else:
            app.logger.debug("alter_question_permissions(): Incorrect parameters passed")
            return False
    except NameError:
        app.logger.debug("alter_question_permissions(): Undefined parameters passed")
        return False
    except SQLAlchemyError:
        app.logger.debug("alter_question_permissions(): Database error")
        return False
