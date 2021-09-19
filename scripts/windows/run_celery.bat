call c:\Data\Websites\RiverCurePortal\venv\Scripts\activate
call c:\Data\Websites\RiverCurePortal\scripts\windows\env.cmd
celery -A rivercureproject worker -l info -P gevent -f celery.logs
