Installation
============
In this section we'll go step-by-step on how to install
the RCP (Rivercure Project) on your local machine for development.


Requirements
------------
The requirements for install the RCP are:

- A machine using Windows, Mac OS or any Linux distro
- `Python <https://www.python.org>`__ 3.0 or above
- Git CLI installed (optinally, you can use `Github Desktop <https://desktop.github.com>`__)
- Access to the RCP Github repository. You can ask any developer for it

Setting up the database
-----------------------
RCP uses a `Postgres <https://www.postgresql.org>`__ database.
The recommended version (the one used in the production server) is the
12.3, however the latest version (by the time of this writting, version 13.4), should
also work seemingly.

After successfully installing the Postgres client, open up a terminal window an type:

.. code-block:: console

    $ psql -U postgres

You can think of psql as a Postgres manager.
Hopefully, you will only have to use it once. 
In some systems, this way of accessing psql doesn't work.
If this is your case, please let us know and we'll try to help.

You are inside psql if your terminal now looks like this (or in a similar way):

.. code-block::

    postgres=#

Now, write the following command to create the database:

.. code-block::

    postgres=# CREATE DATABASE rcp_db;

Afterwards, create your user:

.. code-block::

    postgres=# CREATE USER rcp_user WITH ENCRYPTED PASSWORD 'rcp_pwd';

Then, grant all privileges on the database to the user we just created:

.. code-block::

    postgres=# GRANT ALL PRIVILEGES ON DATABASE rcp_db TO rcp_user;

For the next step, you'll want to enter in the new database context.

.. code-block::

    postgres=# \c rcp_db

Finally, we'll add two project dependencies to our newly created database.
These are related to POSTGIS support, which enables storing geographic-related data in the database.

.. code-block::

    rcp_db=# CREATE EXTENSION postgis;
    CREATE EXTENSION
    rcp_db=# CREATE EXTENSION postgis_raster;
    CREATE EXTENSION

And that's it for the database!

Downloading the RCP to your computer
------------------------------------
Now we're going to install the RCP on our local machine.
For that, please have Github installed and access to the Github repository.

The only thing we have to do is clone the project.

.. code-block:: console

    $ cd a/path/you/like
    $ git clone https://github.com/igamy/Rivercure.git
    (You will probabily be asked to login)
    $ cd Rivercure/

Hurray! Now you are a Rivercure developer 😃

Setting up the virtual environment
----------------------------------
Firstly, let's check our Python version.

.. code-block:: console

    $ python --version

If you are prompted a 2.x.x version, try:

.. code-block:: console

    $ python3 --version

Use the way were you are prompted a 3.x.x version.
In this tutorial, we'll use **python3** syntax for readability.

Now, create the virtual environment. 
This is useful to keep the dependencies from different projects separated.

.. code-block:: console

    $ python3 -m venv venv

A folder named **venv** should have been created.

Now, enter the virtual environment.

.. code-block:: console

    $ . ./venv/bin/activate

You should see your terminal somewhat similar to this:

.. code-block:: console

    (venv) $

It indicates that the virtual environment is active, thus everything
you install using pip from now on will be project-specific.

Installing the dependencies
---------------------------
Now that we have the virtual enviornment, let's install the project's dependencies.

.. code-block:: console

    (venv) $ pip install -r requirements.txt

A list of packages should be automatically downloaded and installed.

Setting up the RCP
------------------
In order to setup the RCP, we have to first make the database migrations.
This process creates the necessary tables for the project.

Before that, we will setup some aliases to make our job easier.

.. code-block:: console

    (venv) $ . ./aliases.bash

Note: this aliases were made for MacOS system, so not all systems may be compatible.
To see the alias equivelent, just open the **aliases.bash** file and there will be the corresponding commands.

Now, we do:

.. code-block:: console

    (venv) $ makemigrations context
    ...
    (venv) $ makemigrations organization
    ...
    (venv) $ makemigrations rivercureportal
    ...
    (venv) $ makemigrations sensors
    ...
    (venv) $ makemigrations users

This will create the migrations files (present under each app's migration folder).

Finally, we do:

.. code-block:: console

    (venv) $ migrate

This will create all the necessary tables in the database.

Running the RCP
---------------
To run the project, type:

.. code-block:: console

    (venv) $ runserver

This will expose the project in a local port, usually 8000.
Go to your favorite browser, and on the address bar type `<http://localhost:8000>`__


Next steps
----------
Now that you have the project running on your local machine, there are some extra things you want to setup on the platform before you start developing.
Head to the :doc:`configure` section to see more.