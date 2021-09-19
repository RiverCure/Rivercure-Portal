Configure and create initial boilerplate data
=============================================
We have to configure some things, specially about the platform's authorization roles.
(For further info on that, go to the :doc:`authorization` document page).


(Recommended) Authorization roles
---------------------------------
To setup the roles, type:

.. code-block:: console

    (venv) $ shell
    ... (Enters Python Interactive Console)
    >>> from rivercureproject.load import run
    >>> run()

The three platform roles: Admin, Manager and Visitor, should have been created now.

(Critical) Super user
---------------------
To create a super user, type:

.. code-block:: console

    (venv) $ python manage.py createsuperuser

Then, follow the steps to create a superuser with the credentials you prefer.

Afterwards, we have to assign the superuser the platform's admin role.
For that, first **login** into the platform with the recently created superuser credentials.
Once logged in, on the navigation bar, select Admin->Admin Backoffice.
If you are prompted to insert credentials, insert the superuser's.
Next, go to the Users tab, select your user, and go to the Groups section.
There, select the Admin group (double click, the Admin role should go to the right side box).
Click save.

Now your user is a platform Admin!

(Recommended) Create Hydrofeatures
----------------------------------
To create the hydrofeatures, type:

.. code-block:: console

    (venv) $ shell (or python manage.py shell)
    ... (Enters Python Interactive Console)
    >>> from rivercureportal.load import run
    >>> run()

A set of hydrofeatures should have been created.

(Optional) Create Hydrofeatures
----------------------------------
To create the hydrofeatures, type:

.. code-block:: console

    (venv) $ shell (or python manage.py shell)
    ... (Enters Python Interactive Console)
    >>> from rivercureportal.load import run
    >>> run()

A set of hydrofeatures should have been created.