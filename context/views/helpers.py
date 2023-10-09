import os
import signal
from context.models import e_Context, e_ContextEvent
from rivercureproject.settings import FILES_BASE_PATH, BASE_DIR, MEDIA_ROOT
from celery import current_app
from shutil import copyfile


def get_context_folder_path(tag):
    return os.path.join(FILES_BASE_PATH, f'{tag}_simulation')


def get_event_folder_path(tag):
    return os.path.join(get_context_folder_path(tag), 'output')


def get_event_rasters_folder_path(tag):
    return os.path.join(get_event_folder_path(tag), 'rasters')


def get_event_rasters_files(tag):
    folder = get_event_rasters_folder_path(tag)
    files = {}
    maxDepth = os.path.join(folder, 'Max_Depth.tif')
    files['maxDepth'] = maxDepth if os.path.exists(maxDepth) else None

    maxLevel = os.path.join(folder, 'Max_Level.tif')
    files['maxLevel'] = maxLevel if os.path.exists(maxLevel) else None

    maxQ = os.path.join(folder, 'Max_Q.tif')
    files['maxQ'] = maxQ if os.path.exists(maxQ) else None

    maxVel = os.path.join(folder, 'Max_Vel.tif')
    files['maxVel'] = maxVel if os.path.exists(maxVel) else None

    return files


def copy_file_to_media_folder(file_path, dest_name):
    try:
        dest = os.path.join(MEDIA_ROOT, dest_name)
        return copyfile(file_path, dest)
    except:
        return None


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
