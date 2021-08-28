from celery import shared_task
import datetime
import requests
import geojson
from .models import e_ContextDTMFile, e_ContextFrictionCoeff
from celery.utils.log import get_task_logger
from context.models import e_Context
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from celery_progress.backend import ProgressRecorder


logger = get_task_logger(__name__)


@shared_task(bind=True)
def preprocess_task(self, url, context_code):
    from .views import prepare_domain, prepare_alignment, prepare_refinement, prepare_boundaries, prepare_boundary_points
    context = e_Context.objects.get(code=context_code)
    try:
        #------------------ Domain --------------------------------
        domain_file = prepare_domain(context_code)
        context_name = domain_file['name']
        #------------------ Alignment --------------------------------
        alignment_file = prepare_alignment(context_code, context_name)
        #------------------ Refinement --------------------------------  
        refinement_file = prepare_refinement(context_code, context_name)
        #------------------ Boundary --------------------------------
        boundary_file = prepare_boundaries(context_code, context_name)
        #------------------ Boundary Points --------------------------------
        boundary_point_file = prepare_boundary_points(context_code, context_name)
        #endof json preparation

        files = {
            'domain.geojson': ('domain.geojson', geojson.dumps(domain_file)),
            'refinements.geojson': ('refinements.geojson', geojson.dumps(refinement_file)),
            'boundaries.geojson': ('boundaries.geojson', geojson.dumps(boundary_file)),
            'boundaries_points.geojson': ('boundaries_points.geojson', geojson.dumps(boundary_point_file)),
        }  
        if alignment_file is not None:
            files['alignments.geojson'] = ('alignments.geojson', geojson.dumps(alignment_file))

        try:
            dtm_file = e_ContextDTMFile.objects.get(context__code=context_code).raster
            files['dtm.tif'] = ('dtm.tif', dtm_file)
        except Exception:
            print('No DTM defined')

        try:
            friction_coeff_file = e_ContextFrictionCoeff.objects.get(context__code=context_code).raster
            files['frictionCoef.tif'] = ('frictionCoef.tif', friction_coeff_file)
        except Exception:
            print('No friction coef defined')

        # Send file
        encoder = MultipartEncoder(files)
        progress_recorder = ProgressRecorder(self)
        files_len = encoder.len

        def my_callback(monitor):
            # print(monitor.bytes_read)
            progress_recorder.set_progress(monitor.bytes_read, files_len)

        payload = {'context_name': context_name}
        monitor = MultipartEncoderMonitor(encoder, my_callback)
        r = requests.post(url, data=monitor, params=payload,  headers={'Content-Type': monitor.content_type})

        return 'OK'
    except Exception as e:
        print(f'Exception:{e}')
        return f'Exception:{e}'


@shared_task(bind=True)
def simulate_task(self, url, context_code, event_id, writing_perio, max_update_perio, writing_unit, update_unit, init_date, end_date, init_time, end_time):
    from .views import prepare_frequency_file, prepare_time_file, prepare_boundaries_file, prepare_gauge_file
    context = e_Context.objects.get(code=context_code)

    # Prepare files
    try:
        print("preparing files...")
        frequency_file = prepare_frequency_file(writing_perio, max_update_perio, writing_unit, update_unit)
        print("frequency OK")
        time_file = prepare_time_file(init_date, end_date, init_time, end_time)
        print("time OK")
        boundary_file = prepare_boundaries_file(context)
        print("boundary OK")
        files = prepare_gauge_file(context, init_date, end_date, init_time, end_time)
        print("gauge OK")

        files.append(('frequency', frequency_file))
        files.append(('time', time_file))
        files.append(('boundaries', boundary_file))
        print("append OK")

        # Send file
        encoder = MultipartEncoder(files)
        progress_recorder = ProgressRecorder(self)
        files_len = encoder.len

        def my_callback(monitor):
            # print(monitor.bytes_read)
            progress_recorder.set_progress(monitor.bytes_read, files_len)

        payload = {'context_name': context.Name, 'event_id': event_id}
        monitor = MultipartEncoderMonitor(encoder, my_callback)
        r = requests.post(url, data=monitor, params=payload,  headers={'Content-Type': monitor.content_type})
    
        return 'OK'
    except Exception as e:
        print(f'Exception:{e}')
        print(e.with_traceback())
        return f'Exception:{e}'