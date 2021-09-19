call c:\Data\Websites\RiverCurePortal\venv\Scripts\activate
call env.cmd
celery -A rivercureproject worker -l info -P gevent -f celery.logs
