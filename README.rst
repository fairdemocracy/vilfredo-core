.. -*- coding: utf-8 -*-

======================
vilfredo-reloaded-core
======================

Vilfredo (Reloaded)
===================


Vilfredo (Reloaded) is a collaborative consensus-building and decision-making tool for generating 
universally supported solutions to open questions (questions which cannot be answered with
a simple 'yes' or 'no'). 

It is entirely egalitarian in that all participants are actively encouraged
to submit, amend and endorse as many proposals as they wish, and by including as many interested parties 
as possible in the decision making process the likelihood is that solutions reached will
have a much greater chance of addressing all possible concerns and stand a better chance of being
successfully implemented due to their wide support.

The system is inherently simple to use. A question is asked and interested parties are invited to
participate. There follows a number of rounds made up of two phases: writing and voting, which lasts
until some kind of consensus is reached. The imposed cycle brings order to the deliberations. During
the writing phase proposals are written or rewritten, then during the voting phase the participant 
has the opportunity to vote and revote as many times as he wishes on those proposals.

Participants are guided throughout the process by helpful 
hints from the system and is presented with an interactive voting map (one of Vilfredo's most novel features)
which allows them to visualise the current status of the deliberation: who currently votes for what, 
who agrees with whom and which proposals are currently winning. This map updates as the voting changes so
participants can immediately see the effects of their votes on the entire system.

Following the voting phase the winning proposals are selected to be included in the next round. These
winning proposals are selected in such a way that every participant has at least one proposal they support
included.

Eventually either a full or a partial consensus is reached (sometime a full consensus is impossible - this is
the nature of free open discussions), and it is up to the group to decide when a deliberation should end.


This package is the core of the application.


Developer Instructions
======================


Requirements
------------

This guide assumes that you develop ``vilfredo-reloaded-core`` on a ``Debian/GNU
Linux`` version ``Wheezy``.

.. code:: sh

    sudo apt-get install python-virtualenv \
    libsqlite3-0


Virtualenv
----------

There are several tools that help to manage python virtualenvs.
If you are already familiar with ``virtualenvwrapper`` you can use it.
If not just follow the following suggestions:

.. code:: sh

    cd
    mkdir ve
    cd ve
    vitutualenv vilfredo-ve
    . vilfredo-ve/bin/activate

.. warning::

    Remember to activate the virtualenv every time you start developing.


Source code
-----------

The source code is manage with ``git`` using the ``git-flow`` work-flow.

You should have an account with writing privileges.

.. code:: sh

    cd
    mkdir vilfredo
    cd vilfredo
    git clone git@git.ahref.eu:vilfredo/vilfredo-reloaded-core.git
    cd vilfredo-reloaded-core
    git checkout -b develop origin/develop


Development
-----------

``vilfredo-reloaded-core`` is developed as a python packages.  The ``develop``
command will download and install the requirements.

.. code:: sh

    python setup.py develop

You can start developing following the issues for your milestone.


Testing
-------

``vilfredo-reloaded-core`` follow a strict testing procedure.  Before every
commit you must check that the test pass and that the source code respect the
best practices defined by the ``python`` community.

.. code:: sh

    python setup.py test
    python setup.py flake8

An improved test runner is:

.. code:: sh

    nosetests -c nose.cfg

This will open a ``ipdb`` shell in case of errors and failures and provide a
coverage report.
