# -*- coding: utf-8 -*-
#
# This file is part of VilfredoReloadedCore.
#
# Copyright (c) 2013 Daniele Pizzolli <daniele@ahref.eu>
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
This file contains code related to the database
'''

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import create_session, scoped_session
from sqlalchemy.ext.declarative import declarative_base

engine = None

db_session = scoped_session(
    lambda: create_session(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )
)

Base = declarative_base()
Base.query = db_session.query_property()


def init_engine(uri, **kwargs):
    # Non so easy to explain: see:
    # http://flask.pocoo.org/snippets/22/
    global engine
    kwargs.setdefault('convert_unicode', True)
    engine = create_engine(uri, **kwargs)
    return engine


def init_db():
    '''
    Create the database using defined models
    '''
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    # pylint: disable=W0611 flake8: noqa
    from . import models

    Base.metadata.create_all(bind=engine)


def drop_db():
    '''
    Drop the database
    '''
    # TODO: this could be slower than a native query
    meta = MetaData(engine)
    meta.reflect()
    meta.drop_all()
