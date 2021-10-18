Improvements
============

There are some improvements that can be done to RCP that would allow a better user experience.
This improvements haven't been implemented yet because they're not priority.

Progress on event preparation
-----------------------------

Websockets for mesh/event generation and notifications update
-------------------------------------------------------------
Currently, for the mesh/event generation, the portal verifies every x seconds if the mesh/event
has been generated. This could be improved to reduce the number of requests to the server,
by using websockets to inform the client, from the server.