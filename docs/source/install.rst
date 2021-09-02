Installation
============
In this section we'll go step-by-step on how to install
the RCP (Rivercure Project) on your local machine for development.


Requirements
------------
The requirements for install the RCP are:

- A machine using Windows, Mac OS or any Linux distro
- `Python <https://www.python.org>`__ 3.0 or above

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

Finally, we'll add two project dependencies to our newly created database.
These are related to POSTGIS support, which enables storing geographic-related data in the database.