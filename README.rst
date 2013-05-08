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
