.. -*- coding: utf-8 -*-

======================
vilfredo-reloaded-core
======================

vilfredo-reloaded is a consensus-building and decision-making tool.

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


Installed under Mac osx 10.8.3, using Sourcetree
------------------------------------------------


start by installing homebrew (I already had it in), makes sure the version of brew you have is up to date
    brew up 
then install python and clean up
    pip install python
    brew cleanup

install virtualenv

    pip install virtualenv

once virtualenv is installed, create a directory where you want to store your virtual environments:

    mkdir test-virtualenv

then go there:

    ls test-virtualenv
    cd test-virtualenv/

now inside there start a new virtual environment:

    virtualenv test-vilfredo

Then activate it

    . test-vilfredo/bin/activate

(When at the end you will want to deactivate the virtualenv write:
        deactivate
)

using Source Tree:

    Open sourcetree and clone the project:

        git@git.ahref.eu:vilfredo/vilfredo-reloaded-core.git

    chosing the directory. I used Desktop/projects/vilfredo-reloaded-core/

(if not go to the directory where you want to clone it and type:

    git  clone git@git.ahref.eu:vilfredo/vilfredo-reloaded-core.git

-I think-)

then go to the directory and check that the project is there

    cd Desktop/projects/vilfredo-reloaded-core/

    ls

    python setup.py develop

You might receive errors if you do not have sqlalchemy and flask installed. In which case
        pip install flask
        pip install sqlalchemy
    and then again
        python setup.py develop 

once you have run the develop and installed everything. You run it
    vr
this will also open a server to where you can point your browser. To break CONTROL+C

Now you want to check that everything is ok. And you do this by running:
    python setup.py test

And then you run flake8 that checks your code and gives you error for any element that is not written in a standard way:
    python setup.py flake8


