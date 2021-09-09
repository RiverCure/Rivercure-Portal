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

Installing the RCP
------------------

Firstly, let's check our Python version.

.. code-block:: console

    $ python --version

If you are prompted a 2.x.x version, try:

.. code-block:: console

    $ python3 --version

Use the way were you are prompted a 3.x.x version.
In this tutorial, we'll use **python3** syntax for readability.