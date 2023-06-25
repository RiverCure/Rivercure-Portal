from celery import shared_task
import requests
import geojson
from .models import e_ContextDTMFile, e_ContextEvent, e_ContextFrictionCoeff
from celery.utils.log import get_task_logger
from context.models import e_Context
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from celery_progress.backend import ProgressRecorder


logger = get_task_logger(__name__)


@shared_task(bind=True)
def preprocess_task(self, url, organizationCode, contextCode):
    from .views import prepare_domain, prepare_alignment, prepare_refinement, prepare_boundaries, prepare_boundary_points
    context = e_Context.objects.get(organization__code=organizationCode, code=contextCode)
    try:
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
            'domain.geojson': ('domain.geojson', geojson.dumps(domain_file)),
            'refinements.geojson': ('refinements.geojson', geojson.dumps(refinement_file)),
            'boundaries.geojson': ('boundaries.geojson', geojson.dumps(boundary_file)),
            'boundaries_points.geojson': ('boundaries_points.geojson', geojson.dumps(boundary_point_file)),
        }
        if alignment_file is not None:
            files['alignments.geojson'] = ('alignments.geojson', geojson.dumps(alignment_file))

        try:
            dtm_file = e_ContextDTMFile.objects.get(context__code=context.code).raster
            files['dtm.tif'] = ('dtm.tif', dtm_file)
        except Exception:
            print('No DTM defined')

        try:
            friction_coeff_file = e_ContextFrictionCoeff.objects.get(context__code=context.code).raster
            files['frictionCoef.tif'] = ('frictionCoef.tif', friction_coeff_file)
        except Exception:
            print('No friction coef defined')

        # Send file
        encoder = MultipartEncoder(files)
        progress_recorder = ProgressRecorder(self)
        files_len = encoder.len

        def my_callback(monitor):
            progress_recorder.set_progress(monitor.bytes_read, files_len)

        payload = {'organizationCode': organizationCode, 'contextCode': contextCode}
        monitor = MultipartEncoderMonitor(encoder, my_callback)
        requests.post(url, data=monitor, params=payload,  headers={'Content-Type': monitor.content_type})

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
