# Rivercure Portal

RiverCure web app. Follow this instrutions to set it up on your computer.

## Needed software:

    1. OSGeo (GDAL, PROJ.4, GEOS)
    2. The libraries in requirements.txt
    3. Python 3.8

## Necessary environment variables:

    1. DATABASE_HOST
    2. DATABASE_URL
    3. DATABASE_PORT
    4. DATABASE_USER
    5. DATABASE_PASSWORD
    4. DATABASE_NAME
    5. CONTEXT_API = {rivercure_portal_url}
    6. SIMULATOR_ADDRESS = {simulation_api_url}
    7. DEBUG = True for dev and test env | False for production

## Configuration:

    1. Download the repo (e.g.: to `/Rivercure`)
    2. Go to the directory: `cd Rivercure/`
    3. Install Python
    4. Install Python-venv: `python3 -m pip install --user virtualenv`
    5. Create a Python virtual environment: `python3 -m venv venv`
    6. Activate the virtual environment: `. venv/bin/activate`
    7. Install the requirements: `python -r requirements.txt`
    8. (Configure Database)
    9. ...

### Create groups:

    1. (After creating a superuser)
    2. Run the server: `python manage.py runserver`
    3. Login as the superuser
    4. In the navigation bar, click 'Admin' -> 'Admin Backoffice'
    5. Click 'Groups' and then create 2 separate groups: 'Admin', 'Manager' and 'Visitor' (case sensitive). When creating the two groups, no permission needs to be added.
    6. Add the superuser as a platform Admin: in the Backoffice, click 'Users' on the left, and then on the admin user
    7. On the user edit page, add the group 'Admin' to the superuser

## Load Hydrofeatures:

    1. Start Django shell: `python manage.py shell`
    2. In the shell, import the load function: `from rivercureportal import load`
    3. Run the routine: `load.run()`
    4. Leave the Django shell: `CTRL+D`

## Database configuration:

    1. PostGres 12.3
    2. CREATE EXTENSION postgis;
    3. CREATE EXTENSION postgis_raster;

    Link: https://postgis.net/install/

## Migrations:

    Before starting these procedures you must have the environment setup and linked to the DB
    1. Save a folder for the data inside the corresponding apps
    2. Enter django shell (python manage.py shell):
        - Import load from {app}
        - input load.run() on cmd
        - The apps that have important data to be loaded are
            1. context
            2. rivercureportal
            3. sensors
            4. rivercureproject
        -
    3. Load an already created context
        1. Start the server
        2. Go to {your_url}/admin/context/e_context/
        3. Create a context, give it a name and save it
        4. Go to {your_url}/contexts/ and click on the context just created
        5. Click upload files
        6. Upload respective files according to their names (It is not necessary to upload all the files at once)
