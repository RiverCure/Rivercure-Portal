import json, os, geojson, tempfile, datetime, requests
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from django.db import transaction, connection
from django.utils import timezone
from ..forms import ContextForm, UploadContextForm, EventForm
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.edit import FormView
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from ..models import e_Context, e_ContextDTM, e_ContextDTMFile, e_ContextFrictionCoeff, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextRefinement, e_ContextAlignment, e_ContextEvent, e_ContextSensor, e_ContextEventResult
from raster.models import RasterLayer
from sensors.models import e_Sensor, e_SensorObservation
from rest_framework import viewsets
from django.core.serializers import serialize
from ..serializers import ContextSerializer
from django.contrib.gis.geos import MultiLineString, MultiPolygon, Polygon, LineString, GEOSGeometry, Point, fromfile
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from ..filters import EventFilter, ContextFilter, ContextSensorFilter
from django.contrib.gis.gdal import SpatialReference, CoordTransform, GDALRaster
from io import BytesIO, StringIO
from zipfile import ZipFile
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django import forms
from pprint import pprint
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import reverse_lazy
from context.forms import ContextDetailsForm
from organization.models import Membership, Organization
from ..tasks import preprocess_task
from notifications.signals import notify
from .authorization import *
from .prepare_files import *
from .upload import boundaryline_creation
from context.views.upload import alignment_creation, context_creation, refinement_creation

class ContextDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView ):
    model = e_Context
    context_object_name = 'context'
    template_name = 'context/e_context_confirm_delete.html'
    success_url = reverse_lazy('context-list')

    def delete(self, *args, **kwargs):
        context : e_Context = self.get_object()

        # Delete DTM and frictionCoef files
        if os.path.exists(f'media/{context.Name}_dtm.tif'):
            os.remove(f'media/{context.Name}_dtm.tif')

        if os.path.exists(f'media/{context.Name}_frictionCoef.tif'):
            os.remove(f'media/{context.Name}_frictionCoef.tif')

        return super(ContextDeleteView, self).delete(*args, **kwargs)

    def test_func(self):
        return context_organization_edit_permission_check(self.request.user, self.get_object().organization)

class ContextUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView ):
    model = e_Context
    form_class = ContextDetailsForm
    context_object_name = 'context'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context['current_view'] = 'edit'
        return context
    
    def get_success_url(self):
        return reverse('context-detail',args=(self.object.code,))

    def test_func(self):
        return context_organization_edit_permission_check(self.request.user, self.get_object().organization)

@login_required
def ContextListView(request):
    
    organizations = Organization.objects.filter(membership__in=Membership.objects.filter(user=request.user, access_granted=True))
    context_list = e_Context.objects.filter(organization__in=organizations)

    context_filter = ContextFilter(request.GET, queryset=context_list, organizations=organizations)

    # Needs to have permission to add in, at least, one organization. The choice list in add form is then filtered to the ones he is actually capable of adding
    permission_to_add = context_general_create_permission_check(request.user)

    context = {
        'permission_to_add': permission_to_add,
        'filter' : context_filter
    }

    return render(request, 'context/e_Context_list.html', context)

@login_required
def OtherContextListView(request):
    # Exclude (the contexts) with organizations the user is in
    other_context_list = e_Context.objects.exclude(organization__in=Organization.objects.filter(members=request.user)).exclude(isPublic=False)
    other_context_filter = ContextFilter(request.GET, queryset=other_context_list, organizations=Organization.objects.exclude(members=request.user))

    context = {
        'context_list': other_context_list,
        'filter': other_context_filter
    }
    return render(request, 'context/e_OtherContext_list.html', context)


class ContextInitialForm(forms.ModelForm):
    class Meta:
        model = e_Context
        fields = ['code','Name', 'hydroFeature', 'organization', 'isPublic',]

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        super(ContextInitialForm, self).__init__(*args, **kwargs)
        # We only want to allow to choose options where the user is org_manager or org_contextManager of the organization
        memberships = Membership.objects.filter(user_id=user_id, access_granted=True, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_contextManager'))
        self.fields['organization'].queryset = Organization.objects.filter(membership__in=memberships)
    

class ContextCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = e_Context
    form_class = ContextInitialForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_view'] = 'create'
        return context

    def get_form_kwargs(self):
        kwargs = super(ContextCreateView, self).get_form_kwargs()
        kwargs.update({'user_id': self.request.user.id})
        return kwargs

    def form_valid(self, form):
        currentTime = datetime.datetime.now()
        organization = form.save(commit=False)
        # Add metadata to organization
        organization.creator = self.request.user
        organization.create_date = currentTime
        organization.save()

        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('context-list')

    def test_func(self):
        return context_general_create_permission_check(self.request.user)

class ContextDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = e_Context
    context_object_name = 'context'
    template_name = 'context/e_Context_detail.html'

    def test_func(self, *args , **kwargs):
        context = self.get_object()
        return context.isPublic or Membership.objects.filter(user=self.request.user, organization=context.organization).exists()

    def get_context_data(self, **kwargs):
        user = self.request.user
        organization = self.get_object().organization

        web_host = os.environ['CONTEXT_API']
        context = super().get_context_data(**kwargs)
        context['api'] = f'http://{web_host}/contexts/api/context/'
        context['sensors'] = get_context_sensors(self.get_object().pk)
        context['form'] = UploadContextForm()
        context['canEdit'] = context_organization_edit_permission_check(user, organization)

        return context

@login_required
def ContextSensorListView(request, context_code):
    context = get_object_or_404(e_Context, code=context_code)
    
    if not( context.isPublic or belongs_to_organization(request.user, context.organization)):
        return HttpResponseRedirect(reverse('context-detail', kwargs={'pk': context.code}))
    
    context_sensor_list = e_ContextSensor.objects.filter(boundary_point__contextBoundaryLine__context__code=context.code).distinct('sensor')

    context_sensor_filter = ContextSensorFilter(request.GET, queryset=context_sensor_list)
    
    context= {
        'filter' :  context_sensor_filter,
        'context': context
    }

    return render(request, 'context/e_ContextSensor_list.html', context )

def get_context_sensors(context_code):
    context_sensors = e_Sensor.objects.filter(isPublic=True, organization__is_active=True)
    context_sensors = context_sensors | e_Sensor.objects.filter(organization=e_Context.objects.get(pk=context_code).organization, organization__is_active=True)
    
    previous_context_sensors = set()
    for elem in e_ContextSensor.objects.filter(boundary_point__contextBoundaryLine__context=get_object_or_404(e_Context, pk=context_code)):
        previous_context_sensors.add(elem.sensor.pk)
    # Adds previously added sensors (from other organizations that are suspended) to the queryset
    context_sensors = context_sensors | e_Sensor.objects.filter(pk__in=previous_context_sensors)
    return context_sensors

def manage_context(request, context_code):
    web_host = os.environ['CONTEXT_API']

    context = {
        # 'contexts': e_Context.objects.filter(user__username=request.user).order_by('Name'),
        # 'sensors': e_Sensor.objects.filter(isPublic=True) | e_Sensor.objects.filter(organization=e_Context.objects.get(pk=context_code).organization),
        'sensors': get_context_sensors(context_code),
        'form': ContextForm(),
        'api': f'http://{web_host}/contexts/api/context/',
        # 'context': request.GET.get('context_code'),
    }
    if request.method == 'POST':
        if not request.user.is_authenticated: # if user is not authenticated
            return render(request, 'context/context.html', context)
        
        form = ContextForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    e_context = context_creation(form, request.user)
                    e_context.save()

                    # initialize and save refinement
                    refinement_creation(form, e_context)
                    # initialize and save alignment
                    alignment_creation(form, e_context)

                    # initialize and save boundaries & boundary points
                    boundaryline_creation(form, e_context)

                messages.success(request,f'Context updated with success!') 
                
                return HttpResponseRedirect(reverse('context-detail', kwargs={'pk': e_context.code}))
            except Exception as e:
                print(f'Error saving context: {e}')
                messages.warning(request,f'Context update failed')

        else:
            messages.warning(request,f'Context info is not complete') 
    else:
        context['context'] = e_Context.objects.get(code=context_code)

    return render(request, 'context/context.html', context)

class ContextViewSet(viewsets.ModelViewSet):
    queryset = e_Context.objects.all()
    lookup_field = 'code'
    serializer_class = ContextSerializer

@login_required
def download_context(request, context_code): #function that allows the download of an context
    if not context_organization_edit_permission_check(request.user, e_Context.objects.get(code=context_code).organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    message = None  #Message to send to user in case of failure
    #prepare geojson for download

    #Need to check if context code exists
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

        mem_file = BytesIO() #memory where the zip file will be created
        with ZipFile(mem_file, 'w') as zipFolder: #create a zipped folder to return to the user
            zipFolder.writestr(f'{context_name}_domain.geojson', geojson.dumps(domain_file))
            if alignment_file is not None:
                zipFolder.writestr(f'{context_name}_alignments.geojson', geojson.dumps(alignment_file))
            if refinement_file is not None:
                zipFolder.writestr(f'{context_name}_refinements.geojson', geojson.dumps(refinement_file))
            if boundary_file is not None:
                zipFolder.writestr(f'{context_name}_boundaries.geojson', geojson.dumps(boundary_file))
            if boundary_point_file is not None:
                zipFolder.writestr(f'{context_name}_boundaries_points.geojson', geojson.dumps(boundary_point_file))

        mem_file.seek(0)
        response = FileResponse(mem_file, content_type="application/zip")
        response['Content-Disposition'] = f'attachment; filename="{context_name}.zip"'
        return response
    except Exception as e:
        messages.warning(request,f'Context not complete for download') 
        print(f'Error downloading context: {e}')
        return redirect(request.META['HTTP_REFERER'])

@login_required
def request_pre_processing(request, context_code):
    context = get_object_or_404(e_Context, code=context_code)
    if not context_organization_edit_permission_check(request.user, context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)
        
    simulator_address = os.environ['SIMULATOR_ADDRESS']
    url = simulator_address + 'process/'

    try:
        r = requests.get(simulator_address) # ping HiSTAV to check if it's online
        result = preprocess_task.delay(url, context_code)
        # Combination hasMesh = False + task_id = val means it's processing
        context.hasMesh = False # Assume there is no mesh generated
        context.task_id = result.task_id
        context.requester = request.user
        context.save()
        messages.success(request, 'Mesh generation request sent')
    except: # HiSTAV not online
        messages.error(request, 'Couldn\'t connect to HiSTAV')

    # if 'HTTP_REFERER' in request.META:
    #     return redirect(request.META['HTTP_REFERER'])
    # else:
    return redirect('context-detail', pk=context_code)

@login_required
def preprocessing_results(request): # function to redirect the user to the paraviewweb visualizer
    paraviewweb_visualizer_url = 'http://localhost:8090'
    return redirect(paraviewweb_visualizer_url)

@login_required
def download_preprocessing_results(request, context_code): # function to redirect the user to the paraviewweb visualizer
    context = get_object_or_404(e_Context, code=context_code)
    if not context_organization_edit_permission_check(request.user, context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    url = os.environ['SIMULATOR_ADDRESS']
    payload = {'context_name': context.Name}
    request = requests.get(f'{url}pre-processing/results/', params=payload, stream=True)
    print(f'Pre-processing results requested for context {context.Name}')
    response = FileResponse(BytesIO(request.content))
    response['Content-Disposition'] = f'attachment; filename="{context.Name}_mesh.vtk"'

    return response

    # messages.warning(self.request, 'Mesh download failed') 
    # return redirect(reverse('context-detail', kwargs={'pk': context_code}))

# Return last line of output
def get_last_line(status:str):
    if status == "":
        return ""
    lines:list = status.splitlines()
    if lines[-1] == "" or lines[-1].isspace():
        return get_last_line("\n".join(lines[0:len(lines)-1]))
    return lines[-1]

# Enhance this
def get_status(last_line:str):
    if ("Permission denied" in last_line) or ("Fail" in last_line) or ("Error" in last_line):
        return "Fail"
    elif ("all files written in" in last_line) or ("--:--:--" in last_line):
        return "Finished successfully"
    else:
        return "Processing"

@login_required
def mesh_status_progress(request, context_name):
    context = get_object_or_404(e_Context, Name=context_name)
    get_object_or_404(Membership, organization=context.organization, user=request.user)
    simulator_address = os.environ['SIMULATOR_ADDRESS']
    url = simulator_address + 'process-status/'

    try:
        payload = {'context_name': context_name}
        response = requests.get(url, params=payload)
        if response.status_code != 200:
            return HttpResponse(status=400)
        
        body = response.content.decode("utf-8")
        lastline = get_last_line(body)
        status = get_status(lastline)

        # Notification
        if ("Fail" in status) or ("Finished successfully" in status):
            notify.send(sender=context, recipient=context.requester, action_object=context.organization, verb=f"Context {context.Name} has finished its processing with status '{status}'")

        return JsonResponse({'status' : status, 'message' : lastline, 'full_log' : body})
    except: # HiSTAV not online
        # 503 = service unavailable
        return HttpResponse(status=503)
    

def mesh_status_change(request, context_name): # Function to mark mesh has generated
    context = e_Context.objects.get(Name=context_name)
    if request.GET.get('status'):
        context.hasMesh = True
        context.task_id = None # task finished
    else:
        context.hasMesh = False

    context.save()

    return HttpResponse(status=200)


@login_required
def mesh_progress(request, context_code):
    e_context = get_object_or_404(e_Context, code=context_code)
    if not context_organization_edit_permission_check(request.user, e_context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    context = {
        'context': e_context
    }
    
    return render(request, 'context/mesh_progress.html', context)

@login_required
def regenerate_mesh_confirm(request, context_code):
    e_context = get_object_or_404(e_Context, code=context_code)
    if not context_organization_edit_permission_check(request.user, e_context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    context = {
        'context': e_context
    }
    
    return render(request, 'context/regenerate_mesh_confirm.html', context)