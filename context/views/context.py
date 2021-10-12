import os, geojson, datetime, requests
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from django.db import transaction
from ..forms import ContextForm, UploadContextForm
from django.contrib import messages
from ..models import e_Context, e_ContextSensor
from sensors.models import Sensor
from rest_framework import viewsets
from ..serializers import ContextSerializer
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from ..filters import ContextFilter, ContextSensorFilter
from io import BytesIO
from zipfile import ZipFile
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from context.forms import ContextDetailsForm, ContextInitialForm
from organization.models import Membership, Organization
from ..tasks import preprocess_task
from notifications.signals import notify
from .authorization import *
from .prepare_files import *
from .upload import boundaryline_creation
from context.views.upload import alignment_creation, context_creation, refinement_creation
from organization.authorization import belongs_to_organization

class ContextUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_Context
    form_class = ContextDetailsForm
    context_object_name = 'context'
    template_name = 'context/context/form.html'
    pk_url_kwarg = 'contextCode'
    
    def get_success_url(self):
        return reverse('context-detail',args=(self.object.code,))

    def test_func(self):
        return context_organization_edit_permission_check(self.request.user, self.get_object().organization)

class ContextListView(LoginRequiredMixin, ListView):
    model = e_Context
    context_object_name = 'contexts'
    template_name = 'context/context/list.html'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        try:
            if request.session['organizationName'] is not None:
                return super(ContextListView, self).dispatch(request, *args, **kwargs)
            else:
                raise Exception
        except:
            messages.warning(request, 'Please first choose an organization')
            return redirect('organization-list')

    def get_queryset(self):
        organization = get_object_or_404(Organization, name=self.request.session['organizationName'])
        context_list = e_Context.objects.filter(organization=organization)
        self.filter = ContextFilter(self.request.GET, queryset=context_list)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter
        context['permission_to_add'] = context_general_create_permission_check(self.request.user)
        return context

class OtherContextListView(LoginRequiredMixin, ListView):
    model = e_Context
    template_name = 'context/context/otherContext_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = get_object_or_404(Organization, name=self.request.session['organizationName'])
        context['context_list'] = e_Context.objects.exclude(organization=organization).exclude(isPublic=False)
        context['filter'] = ContextFilter(self.request.GET, queryset=context['context_list'])
        return context

class ContextCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = e_Context
    form_class = ContextInitialForm
    context_object_name = 'context'
    template_name = 'context/context/form.html'
    success_url = reverse_lazy('context-list')

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

    def test_func(self):
        return context_general_create_permission_check(self.request.user)

class ContextDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = e_Context
    context_object_name = 'context'
    template_name = 'context/context/detail.html'
    pk_url_kwarg = 'contextCode'

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

    def test_func(self, *args , **kwargs):
        context = self.get_object()
        return context.isPublic or Membership.objects.filter(user=self.request.user, organization=context.organization).exists()

class ContextDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = e_Context
    context_object_name = 'context'
    pk_url_kwarg = 'contextCode'
    template_name = 'context/context/confirm_delete.html'
    success_url = reverse_lazy('context-list')

    def delete(self, *args, **kwargs):
        context : e_Context = self.get_object()
        base_path = 'media/'

        # Delete DTM and frictionCoef files
        if os.path.exists(f'{base_path}{context.Name}_dtm.tif'):
            os.remove(f'{base_path}{context.Name}_dtm.tif')

        if os.path.exists(f'{base_path}{context.Name}_frictionCoef.tif'):
            os.remove(f'{base_path}{context.Name}_frictionCoef.tif')

        for i in os.listdir(base_path):
            if os.path.isfile(os.path.join(base_path,i)) and f'frictionCoef_{context.Name}' in i:
                os.remove(f'{base_path}{i}')

        return super(ContextDeleteView, self).delete(*args, **kwargs)

    def test_func(self):
        return context_organization_edit_permission_check(self.request.user, self.get_object().organization)

class ContextSensorListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = e_ContextSensor
    template_name = 'context/context/contextSensor_list.html'

    def setup(self, request, *args, **kwargs):
        self.context = get_object_or_404(e_Context, code=kwargs['contextCode'])
        return super().setup(request, *args, **kwargs)

    def get_queryset(self):
        context_sensor_list = e_ContextSensor.objects.filter(boundary_point__contextBoundaryLine__context__code=self.context.code).distinct('sensor')
        filter = ContextSensorFilter(self.request.GET, queryset=context_sensor_list)
        return filter.qs

    def get_context_data(self, **kwargs):
        context = super(ContextSensorListView, self).get_context_data(**kwargs)
        filter = ContextSensorFilter(self.request.GET, self.get_queryset())
        context['context'] = self.context
        context['filter'] = filter
        return context
    
    def test_func(self):
        return self.context.isPublic or belongs_to_organization(self.request.user, self.context.organization)

def get_context_sensors(context_code):
    context_sensors = Sensor.objects.filter(isPublic=True, sensorClass__organization__is_active=True)
    context_sensors = context_sensors | Sensor.objects.filter(sensorClass__organization=e_Context.objects.get(pk=context_code).organization, sensorClass__organization__is_active=True)
    
    previous_context_sensors = set()
    for elem in e_ContextSensor.objects.filter(boundary_point__contextBoundaryLine__context=get_object_or_404(e_Context, pk=context_code)):
        previous_context_sensors.add(elem.sensor.pk)
    # Adds previously added sensors (from other organizations that are suspended) to the queryset
    context_sensors = context_sensors | Sensor.objects.filter(pk__in=previous_context_sensors)
    return context_sensors

@login_required
def manage_context(request, contextCode):
    web_host = os.environ['CONTEXT_API']

    context = {
        'sensors': get_context_sensors(contextCode),
        'form': ContextForm(),
        'api': f'http://{web_host}/contexts/api/context/',
    }
    if request.method == 'POST':
        
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
                
                return HttpResponseRedirect(reverse('context-detail', kwargs={'contextCode': e_context.code}))
            except Exception as e:
                print(f'Error saving context: {e}')
                messages.warning(request,f'Context update failed')

        else:
            messages.warning(request,f'Context info is not complete') 
    else:
        context['context'] = e_Context.objects.get(code=contextCode)

    return render(request, 'context/context/manage.html', context)

class ContextViewSet(viewsets.ModelViewSet):
    queryset = e_Context.objects.all()
    lookup_field = 'code'
    serializer_class = ContextSerializer

@login_required
def download_context(request, contextCode): #function that allows the download of an context
    if not context_organization_edit_permission_check(request.user, e_Context.objects.get(code=contextCode).organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    message = None  #Message to send to user in case of failure
    #prepare geojson for download

    #Need to check if context code exists
    try:
        #------------------ Domain --------------------------------
        domain_file = prepare_domain(contextCode)
        context_name = domain_file['name']
        #------------------ Alignment --------------------------------
        alignment_file = prepare_alignment(contextCode, context_name)
        #------------------ Refinement --------------------------------  
        refinement_file = prepare_refinement(contextCode, context_name)
        #------------------ Boundary --------------------------------
        boundary_file = prepare_boundaries(contextCode, context_name)
        #------------------ Boundary Points --------------------------------
        boundary_point_file = prepare_boundary_points(contextCode, context_name)
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
def request_pre_processing(request, contextCode):
    context = get_object_or_404(e_Context, code=contextCode)
    if not context_organization_edit_permission_check(request.user, context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)
        
    simulator_address = os.environ['SIMULATOR_ADDRESS']
    url = simulator_address + 'process/'

    try:
        r = requests.get(simulator_address) # ping HiSTAV to check if it's online
        result = preprocess_task.delay(url, contextCode)
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
    return redirect('context-detail', contextCode=contextCode)

@login_required
def preprocessing_results(request): # function to redirect the user to the paraviewweb visualizer
    paraviewweb_visualizer_url = 'http://localhost:8090'
    return redirect(paraviewweb_visualizer_url)

@login_required
def download_preprocessing_results(request, contextCode): # function to redirect the user to the paraviewweb visualizer
    context = get_object_or_404(e_Context, code=contextCode)
    if not context_organization_edit_permission_check(request.user, context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    url = os.environ['SIMULATOR_ADDRESS']
    payload = {'context_name': context.Name}
    request = requests.get(f'{url}pre-processing/results/', params=payload, stream=True)
    print(f'Pre-processing results requested for context {context.Name}')
    response = FileResponse(BytesIO(request.content))
    response['Content-Disposition'] = f'attachment; filename="{context.Name}_mesh.vtk"'

    return response

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
    
    return render(request, 'context/context/mesh_progress.html', context)

@login_required
def regenerate_mesh_confirm(request, context_code):
    e_context = get_object_or_404(e_Context, code=context_code)
    if not context_organization_edit_permission_check(request.user, e_context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    context = {
        'context': e_context
    }
    
    return render(request, 'context/context/regenerate_mesh_confirm.html', context)

def inform_mesh_status(request, context_code): # Function to inform if mesh is generated
    context = e_Context.objects.get(code=context_code)
    if context.hasMesh:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)