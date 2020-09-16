# Rivercure
Create the following groups:

Administration
ContextAdmin
ContextManager
SensorManager

(to be continued)

Migrations:
    1. Save a folder for the data inside the corresponding apps
    2. Enter django shell (python manage.py shell):
        Import load from app
        input load.run() on cmd

Database configuration:
    1. CREATE EXTENSION postgis;
    2. CREATE EXTENSION postgis_raster;

    Link: https://postgis.net/install/