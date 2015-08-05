.. -*- coding: utf-8 -*-

======================
vilfredo-core
======================

Vilfredo
===================


Vilfredo is a collaborative consensus-building and decision-making tool for generating 
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

This guide assumes that you develop ``vilfredo-core`` on a ``Debian/GNU
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
    virtualenv vilfredo-ve
    . vilfredo-ve/bin/activate

.. warning::

    Remember to activate the virtualenv every time you start developing.


Graphviz
------------

Vilfredo uses Graphviz to create voting graphs, so this needs to be installed.

.. code:: sh

    apt-get install graphviz


Source code
-----------

The source code is manage with ``git`` using the ``git-flow`` work-flow.

You should have an account with writing privileges.

.. code:: sh

    cd
    mkdir vilfredo
    cd vilfredo
    git clone https://github.com/fairdemocracy/vilfredo-core.git
    cd vilfredo-core
    git checkout -b develop origin/develop


Development
-----------

``vilfredo-core`` is developed as a python packages.  The ``develop``
command will download and install the requirements.

.. code:: sh

    python setup.py develop

You can start developing following the issues for your milestone.


Testing
-------

``vilfredo-core`` follow a strict testing procedure.  Before every
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


Installing under Mac osx 10.8.3, using Sourcetree
-------------------------------------------------


start by installing homebrew. Make sure the version of brew you have is up to date

.. code:: sh

    brew up 

then install python and clean up

.. code:: sh

    pip install python
    brew cleanup

install virtualenv

.. code:: sh

    pip install virtualenv

once virtualenv is installed, create a directory where you want to store your virtual environments:

.. code:: sh

    mkdir test-virtualenv

then go there:

.. code:: sh

    ls test-virtualenv
    cd test-virtualenv/

now inside there start a new virtual environment:
.. code:: sh

    virtualenv test-vilfredo

Then activate it

.. code:: sh

    . test-vilfredo/bin/activate

When at the end you will want to deactivate the virtualenv type:
.. code:: sh

	deactivate

Using Source Tree:
------------------

Open sourcetree and clone the project:

.. code:: sh

	https://github.com/fairdemocracy/vilfredo-core.git

choosing the directory. I used Desktop/projects/vilfredo-core/

if not go to the directory where you want to clone it and type:

.. code:: sh

    git  clone https://github.com/fairdemocracy/vilfredo-core.git

then go to the directory and check that the project is there

.. code:: sh

    cd Desktop/projects/vilfredo-core/
    python setup.py develop

once you have run the develop and installed everything. You run it by typing vr in the shell.
this will also open a server to where you can point your browser. To break type CONTROL+C

Now you want to check that everything is ok. And you do this by running:

.. code:: sh

    python setup.py test

And then you run flake8 that checks your code and gives you error for any element that is not written in a standard way:

.. code:: sh

	python setup.py flake8
