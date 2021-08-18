from celery import shared_task
import requests
import geojson
from .models import e_ContextDTMFile, e_ContextFrictionCoeff
from celery.utils.log import get_task_logger
from context.models import e_Context
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from celery_progress.backend import ProgressRecorder


logger = get_task_logger(__name__)


@shared_task(bind=True)
def post_files(self, url, context_code):
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

        # context.hasMesh = False # Assume there is no mesh generated
        # context.save()

        # Send file
        encoder = MultipartEncoder(files)
        progress_recorder = ProgressRecorder(self)
        files_len = encoder.len

        def my_callback(monitor):
            # Your callback function
            print(monitor.bytes_read)
            progress_recorder.set_progress(monitor.bytes_read, files_len)

        payload = {'context_name': context_name}
        monitor = MultipartEncoderMonitor(encoder, my_callback)
        r = requests.post(url, data=monitor, params=payload,  headers={'Content-Type': monitor.content_type})

        return 'OK'
    except Exception as e:
        print(f'Exception:{e}')
        return f'Exception:{e}'