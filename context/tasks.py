from celery import shared_task
import geojson
import subprocess
import os
import shutil
from context.views.helpers import cancel_execution, copy_file_to_media_folder, get_context_folder_path, get_event_maxima_folder_path, get_event_rasters_files, get_event_rasters_folder_path, get_log_folder_path, remove_file_to_media_folder
from context.views.prepare_files import prepare_domain
from rivercureproject import settings
from .models import e_ContextDTMFile, e_ContextEvent, e_ContextFrictionCoeff
from celery.utils.log import get_task_logger
from context.models import e_Context


logger = get_task_logger(__name__)


def prepare_files_preprocessing(context):
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


def run_pre_processor(context: e_Context, files):
    tag = context.tag

    context_folder = get_context_folder_path(tag)
    destination_folder = os.path.join(context_folder, 'gis')
    print(f'Mesh generate request for context {context}')
    logger.info(f'Mesh generate request for context {context}')

    log_path = get_log_folder_path(tag)
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
        proc = subprocess.Popen('./mesh', cwd=destination_folder, stdout=log_f, stderr=log_f)
        context.proc_id = proc.pid
        context.save()

    except Exception as e:
        print(f'Failed pre-processing!\nException{e}')
        import traceback
        traceback.print_exc()
        return False

    return True


@shared_task(bind=True)
def preprocess_task(self, contextCode):
    context = e_Context.objects.get(code=contextCode)
    try:
        cancel_execution(context)
    except:
        context.proc_id = None
        context.save()

    try:
        files = prepare_files_preprocessing(context)
        run_pre_processor(context, files)
        return 'OK'
    except Exception as e:
        print(f'Exception:{e}')
        return f'Exception:{e}'


def prepare_files_simulation(event, writing_perio, max_update_perio, writing_unit, update_unit, init_date, end_date, init_time, end_time):
    from .views import prepare_frequency_file, prepare_time_file, prepare_boundaries_file, prepare_gauge_file
    print("preparing files...")
    frequency_file = prepare_frequency_file(writing_perio, max_update_perio, writing_unit, update_unit)
    time_file = prepare_time_file(init_date, end_date, init_time, end_time)
    boundary_file = prepare_boundaries_file(event.context)
    files_sensors = prepare_gauge_file(event.context, init_date, end_date, init_time, end_time)

    files = {
        'frequency': frequency_file,
        'time': time_file,
        'boundaries': boundary_file,
    }
    files = {**files, **files_sensors}  # puts together all in the same dictionary
    print("Finished preparing files")
    return files


def run_simulator(event, files):
    print("Starting simulation...")
    tag = event.context.tag
    # Remove whitespaces from event name

    context_folder = get_context_folder_path(tag)
    frequency_destination_folder = os.path.join(context_folder, 'output', 'output.cnt')
    sensor_data_destination_folder = os.path.join(context_folder, 'boundary', 'gauges')
    time_destination_folder = os.path.join(context_folder, 'control', 'time.cnt')
    boundary_destination_folder = os.path.join(context_folder, 'boundary', 'boundary.cnt')

    for key in files:
        if key == 'frequency':
            with open(frequency_destination_folder, 'w') as file:
                file.write(files[key])
        if key == 'time':
            with open(time_destination_folder, 'w') as file:
                file.write(files[key])
        if key == 'boundaries':
            with open(boundary_destination_folder, 'w') as file:
                file.write(files[key])
        else:
            # The only case left is sensor data files
            dest_folder = os.path.join(sensor_data_destination_folder, key)
            with open(dest_folder, 'w') as file:
                file.write(files[key])

    # bnd are duplicated might be necessary to remove them
    log_file = get_log_file_path(event)
    try:
        log_f = open(log_file, 'w')
        proc = subprocess.Popen('./solver2D', cwd=context_folder, stdout=log_f, stderr=log_f)
        event.proc_id = proc.pid
        event.save()
    except Exception as e:
        print(f'Failed simulation!\nException{e}')
        import traceback
        traceback.print_exc()
        return False

    return True


def get_log_file_path(event):
    eventName = event.Name.replace(' ', '-')
    tag = event.context.tag
    log_path = get_log_folder_path(tag)
    log_file = os.path.join(log_path, f'{eventName}_simulation_log.txt')
    return log_file


@shared_task(bind=True)
def simulate_task(self, event_id):
    event = e_ContextEvent.objects.get(id=event_id)
    try:
        cancel_execution(event)
    except:
        event.proc_id = None
        event.save()

    # This log file log was placed here instead of in run_simulator to write the "Preparing files line"
    # and prevent that the first few seconds the UI presents an error
    tag = event.context.tag
    log_path = get_log_folder_path(tag)
    log_file = get_log_file_path(event)

    if os.path.exists(log_file):
        os.remove(log_file)

    # Creates folders if they dont exist
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    rasters = get_event_rasters_files(event.context.tag)
    for key in rasters.keys():
        file_name = f'{event.Name}_{key}.tif'
        remove_file_to_media_folder(file_name)

    with open(log_file, 'w') as f:
        f.write('Preparing files...')

    # Prepare files
    try:
        files = prepare_files_simulation(event, event.WritingPeriodicity, event.UpdateMaximumValue,
                                         event.WritingPeriodicityUnit, event.UpdateMaximumValueUnit, event.startDate, event.endDate, event.startTime, event.endTime)
        run_simulator(event, files)
        return 'OK'
    except Exception as e:
        print(f'Exception:{e}')
        return f'Exception:{e}'


@shared_task(bind=True)
def generate_tiffs(self, event_id):
    event = e_ContextEvent.objects.get(id=event_id)

    gis_scripts_path = os.path.join(settings.BASE_DIR, 'gis-scripts')
    rasters_path = get_event_rasters_folder_path(event.context.tag)

    maxima_path = get_event_maxima_folder_path(event.context.tag)
    maxima_files = os.listdir(maxima_path)
    if len(maxima_files) == 0:
        raise Exception('No maxima files found')
    maxima_file = os.path.join(maxima_path, maxima_files[0])

    result = subprocess.Popen(['/usr/bin/python3', 'stavResults.py', '-i', maxima_file,
                               '-o', 'raster_pre', '-e', '3763'], cwd=rasters_path).wait(120)
    if result is None or result < 0:
        raise Exception(f'Calling stavResults.py failed. Return code: {result}')

    domain_file_name = f'{event.context.code}.geojson'
    domain_file_content = geojson.dumps(prepare_domain(event.context.code))
    with open(os.path.join(gis_scripts_path, f'{event.context.code}.geojson'), 'w') as file:
        file.write(domain_file_content)

    raster_file_path = os.path.join(rasters_path, 'raster-Max_Depth.tif')
    domain_cl = event.context.CLExternalBoundary
    cl = domain_cl * (-2.5)
    result = subprocess.Popen(['/usr/bin/python3', 'bufferTiff.py', '-i', domain_file_name,
                               '-o', raster_file_path, '-d', str(cl)], cwd=gis_scripts_path).wait(120)
    if result is None or result < 0:
        raise Exception(f'Calling bufferTiff.py failed. Return code: {result}')

    raster_files_pre = ['raster_pre-Max_Depth.tif', 'raster_pre-Max_Level.tif',
                        'raster_pre-Max_Q.tif', 'raster_pre-Max_Vel.tif']
    raster_files = ['raster-Max_Depth.tif', 'raster-Max_Level.tif', 'raster-Max_Q.tif', 'raster-Max_Vel.tif']
    for raster_file_pre, raster_file in zip(raster_files_pre, raster_files):
        result = subprocess.Popen(['gdalwarp', '-overwrite', '-cutline', 'buffers.shp',
                                   '-crop_to_cutline', raster_file_pre, raster_file], cwd=rasters_path).wait(120)

        if result is None or result < 0:
            raise Exception(f'Calling gdalwarp failed. Return code: {result}')

    rasters = get_event_rasters_files(event.context.tag)
    for key, value in rasters.items():
        file_name = f'{event.Name}_{key}.tif'
        path = copy_file_to_media_folder(value, file_name)
        if path:
            rasters[key] = os.path.join(os.sep, settings.MEDIA_URL, file_name)
        else:
            rasters[key] = None
