from celery import shared_task
import requests
import geojson
import subprocess
import os
import shutil
from .models import e_ContextDTMFile, e_ContextEvent, e_ContextFrictionCoeff
from celery.utils.log import get_task_logger
from context.models import e_Context
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from celery_progress.backend import ProgressRecorder
from django.conf import settings


logger = get_task_logger(__name__)

if settings.TEST_ENV:
    # /mnt/disks/RiverCurePortal
    FILES_BASE_PATH = os.path.join(os.sep, 'mnt', 'disks', 'RiverCurePortal')
else:
    FILES_BASE_PATH = os.path.join(settings.BASE_DIR, 'mnt', 'disks', 'RiverCurePortal')


def get_context_folder_path(organization_code, context_code):
    return os.path.join(FILES_BASE_PATH, f'{organization_code}-{context_code}_simulation')


def prepare_files(context):
    from .views import prepare_domain, prepare_alignment, prepare_refinement, prepare_boundaries, prepare_boundary_points
    # ------------------ Domain --------------------------------
    domain_file = prepare_domain(context.code)
    # ------------------ Alignment --------------------------------
    alignment_file = prepare_alignment(context.code, context.Name)
    # ------------------ Refinement --------------------------------
    refinement_file = prepare_refinement(context.code, context.Name)
    # ------------------ Boundary --------------------------------
    boundary_file = prepare_boundaries(context.code, context.Name)
    # ------------------ Boundary Points --------------------------------
    boundary_point_file = prepare_boundary_points(context.code, context.Name)
    # endof json preparation

    files = {
        'domain.geojson': geojson.dumps(domain_file),
        'refinements.geojson': geojson.dumps(refinement_file),
        'boundaries.geojson': geojson.dumps(boundary_file),
        'boundaries_points.geojson': geojson.dumps(boundary_point_file),
    }
    if alignment_file is not None:
        files['alignments.geojson'] = geojson.dumps(alignment_file)

    try:
        dtm_file = e_ContextDTMFile.objects.get(context__code=context.code).raster
        files['dtm.tif'] = dtm_file
    except e_ContextDTMFile.DoesNotExist:
        print('No DTM defined')
        logger.error(f'DTM file for context {context} is not defined')

    try:
        friction_coeff_file = e_ContextFrictionCoeff.objects.get(context__code=context.code).raster
        files['frictionCoef.tif'] = friction_coeff_file
    except e_ContextFrictionCoeff.DoesNotExist:
        print('No friction coef defined')
        logger.error(f'friction coef file for context {context} is not defined')

    return files


def run_pre_processor(context, files):
    organizationCode = context.organization.code
    contextCode = context.code

    context_folder = get_context_folder_path(organizationCode, contextCode)
    destination_folder = os.path.join(context_folder, 'gis')
    print(f'Mesh generate request for context {context}')
    logger.info(f'Mesh generate request for context {context}')

    log_path = os.path.join(settings.BASE_DIR, 'logs', context.tag)
    log_file = os.path.join(log_path, 'mesh_log.txt')

    # If organization's/context's log folder doesnt exist, create
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # Delete log file for this context if it already exists
    if os.path.exists(log_file):
        os.remove(log_file)

    try:
        shutil.copytree('simulation', context_folder, dirs_exist_ok=True)

        for key in files:
            if key == 'dtm.tif' or key == 'frictionCoef.tif':  # FileFields
                dest = os.path.join(destination_folder, 'rasters', key)
                shutil.copyfile(files[key].path, dest)
            else:
                dest = os.path.join(destination_folder, 'context_files', key)
                with open(dest, 'w') as file:
                    file.write(files[key])

        log_f = open(log_file, 'w')
        # subprocess.Popen(f'''(cd {destination_folder} && ./mesh && cd ../../.. \
        #         && curl {requester_ip}/contexts/mesh-status/{contextCode}/change?organization={organizationCode}\&status=True &)''',
        #         stdout=log_f, stderr=log_f, shell=True)
        subprocess.Popen(f'(cd {destination_folder} && ./mesh &)', stdout=log_f, stderr=log_f, shell=True)

    except Exception as e:
        print(f'Failed pre-processing!\nException{e}')
        import traceback
        traceback.print_exc()
        return 'fail'

    return 'success'


@shared_task(bind=True)
def preprocess_task(self, organizationCode, contextCode):
    context = e_Context.objects.get(organization__code=organizationCode, code=contextCode)

    try:
        files = prepare_files(context)
        run_pre_processor(context, files)
        return 'OK'
    except Exception as e:
        print(f'Exception:{e}')
        return f'Exception:{e}'


@shared_task(bind=True)
def simulate_task(self, url, event_id, writing_perio, max_update_perio, writing_unit, update_unit, init_date, end_date, init_time, end_time):
    from .views import prepare_frequency_file, prepare_time_file, prepare_boundaries_file, prepare_gauge_file
    event = e_ContextEvent.objects.get(id=event_id)

    # Prepare files
    try:
        print("preparing files...")
        frequency_file = prepare_frequency_file(writing_perio, max_update_perio, writing_unit, update_unit)
        time_file = prepare_time_file(init_date, end_date, init_time, end_time)
        boundary_file = prepare_boundaries_file(event.context)
        files_sensors = prepare_gauge_file(event.context, init_date, end_date, init_time, end_time)

        files = {
            'frequency': ('frequency', frequency_file),
            'time': ('time', time_file),
            'boundaries': ('boundaries', boundary_file),
        }
        files = {**files, **files_sensors}  # puts together all in the same dictionary

        # Send file
        encoder = MultipartEncoder(files)
        progress_recorder = ProgressRecorder(self)
        files_len = encoder.len

        def my_callback(monitor):
            progress_recorder.set_progress(monitor.bytes_read, files_len)

        payload = {
            'organizationCode': event.context.organization.code,
            'contextCode': event.context.code,
            'eventName': event.Name,
            'eventId': event.id
        }
        monitor = MultipartEncoderMonitor(encoder, my_callback)
        requests.post(url, data=monitor, params=payload,  headers={'Content-Type': monitor.content_type})

        return 'OK'
    except Exception as e:
        print(f'Exception:{e}')
        return f'Exception:{e}'
