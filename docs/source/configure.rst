Configure and create initial sample data
========================================
We have to configure some things, specially about the platform's authorization roles.
(For further info on that, go to the :doc:`authorization` document page).


(Necessary) Authorization roles
-------------------------------
To setup the roles, type:

.. code-block:: console

    (venv) $ shell
    ... (Enters Python Interactive Console)
    >>> from rivercureproject.load import run
    >>> run()

The three platform roles: Admin, Manager and Visitor, should have been created now.

(Necessary) Super user
----------------------
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

.. _create-first-organization:

(Optional) Create your first organization
-----------------------------------------
Now, let's create a organization.

For that, logged in as a platform Admin, click in the Organization menu.
There, you will see a 'Create Organization' button.

Click on it, introduce a name (e.g.: IST) and a manager. This manager can be the user you are currently logged in.

Now a organization has been created.

.. _create-sensor-class-and-properties:

(Optional) Create your first sensor class and its properties
------------------------------------------------------------
To create your first sensor class, you need to have a organization. 
If you don't have one, follow :ref:`create-first-organization` steps.

Go to the Organization tab. There, click on your organization.
This will lead you to a page with the organization's details and some buttons. 
Click on 'Manage sensor classes'.
Next, click on 'Create sensor class'.
For the next steps to work, create a sensor class with code 'hydrometricSensor', name 'Hydrometric Sensor' and state 'Active'.
The other fields insert as you will and save.

Now that the sensor class has been created, we need to create properties for it.
To do that, click on the sensor class you have just created, then 'Property list' and finally 'Create property'.

We will have to create two properties:

- The first with code 'discharge', name 'Discharge', type 'Number' and optional (optional checkbox checked). You can leave the other fields blank.
- The second with code 'depth', name 'Depth', type 'Number' and optional (optional checkbox checked). You can also leave the other fields blank.

Now you have created your first sensor class and its properties.


(Optional) Create your first sensors and observations
-----------------------------------------------------
Now, let's create some sensors and observations. This requires the sensor class and its properties created at :ref:`create-sensor-class-and-properties`.

Sensors and observations can be created manually (via a form) or uploaded throught Excel files. We'll do the latter.

Head over to the *sample/sensors/Coura* folder. There will be a set of Excel files.

On the browser, open the RCP and log in. Then, click on the 'Sensors' tab. At the end of the page a 'Upload Sensor(s)' button will be present.
Click on it to reveal the upload button. Upload the *RCP_sensors_coura.xlsx* file from *sample/sensors/Coura*.

A success message on the top of the page should appear, as well as some sensors on the list.

Now, to create the observations, do the following steps for each sensor:
- On the list, click on the sensor's code
- Then 'Obsevations'
- Click 'Upload Observation(s)'
- Upload the Excel file corresponding to that sensor (it is on the Excel file name)

After doing that for 6 sensors, you're done!


(Optional) Create your first context
------------------------------------
To create a context, head to the 'Context' tab.
There click on 'Add Context' and set its name and code to 'Coura'. Assign a organization to it.
If you haven't done so, follow :ref:`create-first-organization`.

Next, click on the context you just created and afterwards click on 'GeoEdit' button.

- For the Domain, select the *sample/contexts/Coura/domain.geojson*
- For the Alignments, select the *sample/contexts/Coura/alignments.geojson*
- For the Refinements, select the *sample/contexts/Coura/refinements.geojson*
- For the Boundaries, select the *sample/contexts/Coura/boundaries.geojson*
- For the DTM file, select the *sample/contexts/Coura/dtm_coura.tif*
- For the Friction coefficient file, select the *sample/contexts/Coura/frictionCoef_Coura.tif*

After all the files are selected, click 'Upload'.

Now, the map should have a slightly different layout compared to what you had before. There's your first context!