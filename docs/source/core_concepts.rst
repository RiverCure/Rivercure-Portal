Core concepts
=============

Hydrofeature
------------
A Hydrofeature is an area of water. It can be a river, a lake, a estuary, a dam, etc.
It is represented by its geometry in the RiverCure Portal and is associated with a :ref:`context-definition`.

Organization
------------
An organization is a group of users.
Think of it as real organizations that could be working with the RiverCure, like APA and IST.

Users within an organization can have one of 5 roles: Member, Sensor Manager, Context Manager, Event Manager or Manager.
Information on what each role can do can be found in :doc:`authorization`.

A user can belong to multiple organizations, and have a different role in each one. 
So, a user can be a Manager at IST and a Member at APA.

An organization has sensor classes, which are organization-specific and can't be shared with other organizations.
Contexts and sensors are also organization-specific, but in turn these can be shared with other organizations, by setting its individual property to public or private.

.. _context-definition:

Context
-------

Sensor class & sensor class property
------------------------------------
Think of a sensor class as a sensor model, like the `LU06-A Hydrometric Sensor <https://www.alphaomega-electronics.com/en/sensors-probes/1914-lu06-a-hydrometric-sensor-water-or-snow-level-by-ultrasound-range-0-6m-output-0-10vdc.html>`__.
It has a certain vendor and device version, it is fixed or mobile, and can read a certain properties, like water depth and discharge level.
The properties are represented in the RiverCure Portal as **sensor class properties**.

Sensors & observations
----------------------
Sensors are instances of sensor classes. Following the previous example, we can have multiple `LU06-A Hydrometric Sensor <https://www.alphaomega-electronics.com/en/sensors-probes/1914-lu06-a-hydrometric-sensor-water-or-snow-level-by-ultrasound-range-0-6m-output-0-10vdc.html>`__ sensors deployed in multiple locations.
Because of that, they get different value readings.
These value readings are represented by the concept of **observation**.
An observation has a date, time and value of each property of the sensor's sensor class properties.

Pre-processing
--------------

Event
-----

