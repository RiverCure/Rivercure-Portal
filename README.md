# Rivercure
Create groups and populate through load_groups.py script;
Populate sensors (sensors\load.py);
Populate sensors observations (sensors\load_observations.py);


Migrations:
    1. Save a folder for the data inside the corresponding apps
    2. Enter django shell (python manage.py shell):
        Import load from app
        input load.run() on cmd

Database configuration:
    1. CREATE EXTENSION postgis;
    2. CREATE EXTENSION postgis_raster;

    Link: https://postgis.net/install/

Needed software:
    1. OSGeo (GDAL, PROJ.4, GEOS)
    2. RabbitMQ