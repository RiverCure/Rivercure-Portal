# Rivercure Portal
RiverCure web app. Follow this instrutions to set it up on your computer.

## Needed software:
    1. OSGeo (GDAL, PROJ.4, GEOS)
    2. The libraries in requirements.txt

## Necessary environment variables:
    1. DATABASE_HOST
    2. DATABASE_URL
    3. DATABASE_PORT
    4. DATABASE_USER
    5. DATABASE_PASSWORD
    4. DATABASE_NAME
    5. CONTEXT_API = {rivercure_portal_url}
    6. SIMULATOR_ADDRESS = {simulation_api_url}

## Database configuration:
    1. CREATE EXTENSION postgis;
    2. CREATE EXTENSION postgis_raster;

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