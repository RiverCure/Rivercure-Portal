import os
import signal
from context.models import e_Context, e_ContextEvent
from rivercureproject.settings import FILES_BASE_PATH, BASE_DIR
from celery import current_app


def get_context_folder_path(tag):
    return os.path.join(FILES_BASE_PATH, f'{tag}_simulation')


def get_log_folder_path(tag):
    return os.path.join(BASE_DIR, 'logs', tag)


def cancel_execution(context_or_event):
    '''Kills the existing/previous execution if it exists'''
    pid = context_or_event.proc_id
    if pid:
        os.kill(pid, signal.SIGKILL)
        context_or_event.proc_id = None
        context_or_event.save()


def cancel_task(context_or_event):
    task_id = context_or_event.task_id
    if task_id:
        current_app.control.revoke(task_id)
        context_or_event.task_id = None
        context_or_event.save()
