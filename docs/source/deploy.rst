Deploy
======

RiverCure
---------
The RCP is deployed in a Windows server hosted remotely.
In order to access it, you'll need **TeamViewer**.
To get the access keys, please ask an admin.

Once inside, you'll have a Windows GUI.
This is where you can interact with the remote machine.

The project is at ``C:\Data\Websites\RivercurePortal``.


The actions you will want to do are:

- **Pull changes**: open a terminal on the project directory and type ``git pull``. This will pull the changes made in the Rivercure project to the deployment server.

- **Activate the virtual enviornment**: open a terminal on the project directory and type ``c:\Data\Websites\RiverCurePortal\venv\Scripts\activate``. A ``(venv)`` prefix should appear in the terminal.

- **Make migrations**: If you made any change in a ``(app_name).models.py`` file, you will want to make the database migrations. To do that, first activate the virtual environment as explained in the previous topic. Next, run ``python manage.py makemigrations (app_name)``. This will create the migrations file. Next, do ``python manage.py migrate``. This should migrate the database to match the models.

- **Run the server**: In order to run the server, you have two options: either run in a terminal or run as a process. To run as a process, go to the processes page, find Rivercure and start it. To run it in a terminal, go to the project and type ``.\scripts\windows\run_server.bat``

- **Run celery**: Celery needs to be runing in order for the portal to function correctly. To run it, open a terminal, head to the project directory and type ``.\scripts\windows\run_celery.bat``.

RiverCure shutted down
----------------------
If the RiverCure machine shutdowned for some reason, you will have to do some steps in order for RiverCure to work:
1. Log in to the RiverCure user
2. Go to **Services**, and check if the 'RiverCurePortal' and 'RiverCurePortal-Tasks' services are running. If not, start them, first the *RiverCurePortal* and then the *RiverCurePortal-Tasks*.
3. Connect to the VPN. On the bottom left, there should be a OpenVPN instance running. If not, start it like a normal program. Then, connect to the VPN by opening it and clicking **connect**.

HiSTAV
------
HiSTAV is deployed in a Linux server. To access it, please ask an admin how to.

Once inside, you'll have a GUI. 

What you want to do here is basically update the HiSTAV's code. You'll find it in the desktop folder, in app.py. Here you have to copy and paste all the code to make a change. Then, restart the server that is running in the terminal.