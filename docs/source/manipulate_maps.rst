Manipulating maps
=================
You may want to add some functionality to the maps, but the context.js file may be intimidating.
Don't worry, in this section we will cover the main functions you need to know about and what you can do with them.

sensorAssociationPopupConfig
----------------------------
This function controls the popup when you click in a boundary to associate it with the sensor. This includes a list
of sensors already associated with that boundary and a select to add another.
This you may want to do here:

- **Change the condition that controls whether a sensor can be associated with a boundary or not** - This can be done by going to the for loop that iterates over the sensors at the end of the function, and add a condition there
- **Change the string of the selectable item** - Where it says *option.innerHTML*, just add there