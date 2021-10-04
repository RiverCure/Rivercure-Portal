Authorization
=============

We'll use the following notation:

- C : Create
- R : Read
- U : Update
- D : Delete
- S : Suspend
- A : Activate

There are two level of permissions.

1. **Platform permissions** - Refers to the actions an user can do in the platform
2. **Organization permissions** - Refers to the actions an user that belongs to an organization can do in the organization

Platform permissions
--------------------
There are 3 level of permissions.

- **Admin**: can manage users, hydrofeatures, access the admin backoffice and create/suspend organizations. It has the highest level of platform permissions.

- **Manager**: can manage hydrofeatures

- **Visitor**: no platform-specific permissions

.. csv-table:: Platform permissions by role
   :file: _files/platform_permissions.csv
   :header-rows: 1
   :stub-columns: 1

Organization permissions
------------------------

- **Manager**: can accept/reject organization access requests, edit a member's (that is not a manager) permissions in the organization. Also has every permission of the below roles.

- **ContextManager**: can CRUD contexts, events and sensors of the organization.

- **EventManager**: can CRUD events of the organization, and see everything else.

- **SensorManager**: can CRUD sensors of the organization, and see everything else.

- **Member**: can only see contexts, events and sensors of the organization.

.. csv-table:: Organization permissions by role
   :file: _files/organization_permissions.csv
   :header-rows: 1
   :stub-columns: 1