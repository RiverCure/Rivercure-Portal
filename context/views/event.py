from django.shortcuts import get_object_or_404, render
from context.models import e_Context, e_ContextEvent, e_ContextEventResult
from .authorization import *
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from context.filters import EventFilter
from sensors.models import e_Sensor
import os
from django.contrib import messages
from django.urls import reverse
import requests
from io import BytesIO
from zipfile import ZipFile
from rivercureproject import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from context.forms import EventForm
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from .prepare_files import *
from context.tasks import simulate_task
from notifications.signals import notify

def ContextEventListView(request, context_code):
    context = get_object_or_404(e_Context, pk=context_code)

    if not (context.isPublic or belongs_to_organization(request.user, context.organization)):
        return HttpResponse('Unauthorized', status=401)

    qs = e_ContextEvent.objects.filter(context=context)
    
    event_filter = EventFilter(request.GET, queryset=qs)
    events_list = event_filter.qs
    
    context = {
        'events': events_list,
        'filter': event_filter,
        'context': e_Context.objects.get(code=context_code),
        'hasPerm': context_organization_event_permission_check(request.user, context.organization)
    }
    return render(request, 'context/e_Event_list.html', context)

class EventDetailView(LoginRequiredMixin, DetailView):
    model = e_ContextEvent
    context_object_name = 'event'
    pk_url_kwarg = 'event_id'
    template_name = 'context/e_Event_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context['hasPerm'] = context_organization_event_permission_check(self.request.user, self.get_object().context.organization)
        return context

# TODO: check for permissions
@login_required
def view_events_results(request, event_id): #function to view the results of an event simulation
    event = e_ContextEvent.objects.get(pk=event_id)
    web_host = os.environ['CONTEXT_API']
    
    context = {
        'api': f'http://{web_host}/contexts/api/context/',
        'context': event.context,
        'sensors': e_Sensor.objects.all(),
        'event': event,
        'max_depth': event.context_event_results.max_depth.id,
        'max_level': event.context_event_results.max_level.id,
        'max_q': event.context_event_results.max_q.id,
        'max_vel': event.context_event_results.max_vel.id
    }

    return render(request, 'context/event_results.html', context)


# TODO: check for permissions
@login_required
def download_simulation_results(request, event_id): #function to download simulation results
    url = os.environ['SIMULATOR_ADDRESS']

    try:
        context_event = e_ContextEvent.objects.get(pk=event_id)
    except:
        messages.warning(request, 'Request unsuccesful')
        return HttpResponseRedirect(reverse('event-list'))

    context_name = context_event.context.Name

    payload = {'context_name': context_name, 'event_id': event_id}
    request = requests.get(f'{url}simulation/results/', params=payload, stream=True)

    # mem_file = BytesIO()
    # with ZipFile(mem_file, 'w') as destination:
    #     for chunk in request.iter_content(chunk_size=1024):
    #             destination.write(chunk)

            
    print(f'Simulation results requested for context {context_name} event {event_id}')
    response = FileResponse(BytesIO(request.content))
    response['Content-Disposition'] = f'attachment; filename="{context_name}_{event_id}_simulation_results.zip"'
    return response

def handle_simulation_results(request, event_id): #function to handle simulation results
    sim_url = os.environ['SIMULATOR_ADDRESS']

    event = e_ContextEvent.objects.get(pk=event_id)
    context_name = event.context.Name
    url = f'{sim_url}/simulation/results/?event_id={event_id}&context_name={context_name}'

    try:
        req = requests.get(url)
    except Exception as e:
        print(f'Simulation event handling failed: {e}')
        return HttpResponse(status=404)

    with ZipFile(BytesIO(req.content)) as simulation_results_zip:
        simulation_results_zip.extractall(f'{settings.MEDIA_ROOT}/rasters/')

    try:
        results = event.context_event_results
        results.time = timezone.now()
    except ObjectDoesNotExist:
        results = e_ContextEventResult()
        results.context_event = event
        results.time = timezone.now()

    try:
        results.max_depth = define_raster('Max Depth', f'rasters/results/{context_name}_event_{event_id}-Max_Depth.tif')
        results.max_level = define_raster('Max Level', f'rasters/results/{context_name}_event_{event_id}-Max_Level.tif')
        results.max_q = define_raster('Max Q', f'rasters/results/{context_name}_event_{event_id}-Max_Q.tif')
        results.max_vel = define_raster('Max Vel', f'rasters/results/{context_name}_event_{event_id}-Max_Vel.tif')

        results.save()
    except Exception as e:
        print(f'Simulation results upload failed\nException: {e}')
        return HttpResponse(status=404)

    return HttpResponse(status=200)

class EventCreateView(LoginRequiredMixin,UserPassesTestMixin, CreateView):
    model = e_ContextEvent
    template_name = 'context/e_Event_create.html'
    form_class = EventForm
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context['context'] = get_object_or_404(e_Context, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        context = e_Context.objects.get(code=form.cleaned_data['context_code'])
        writing_period = form.cleaned_data['WritingPeriodicity']
        max_update_period = form.cleaned_data['UpdateMaximumValue']
        writing_unit = form.cleaned_data['WritingPeriodicityUnit']
        update_unit = form.cleaned_data['UpdateMaximumValueUnit']
        init_date = form.cleaned_data['startDate']
        end_date = form.cleaned_data['endDate']
        init_time = form.cleaned_data['startTime']
        end_time = form.cleaned_data['endTime']
        
        obj = form.save(commit=False)
        obj.context = context
        obj.save() 

        return HttpResponseRedirect(reverse('event-detail',args=(context.code, obj.id,)))

    def test_func(self):
        organization = e_Context.objects.get(pk=self.kwargs['pk']).organization
        return context_organization_event_permission_check(self.request.user, organization)

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_ContextEvent
    template_name = 'context/e_Event_create.html'
    form_class = EventForm
    pk_url_kwarg = 'event_id'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['context'] = get_object_or_404(e_Context, pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse('context-event-list',args=(self.get_object().context.code, ))

    def test_func(self):
        return context_organization_event_permission_check(self.request.user, self.get_object().context.organization)


def runsimulationview(request, pk, event_id):
    event = get_object_or_404(e_ContextEvent, id=event_id)
    if not context_organization_event_permission_check(request.user, event.context.organization):
        return HttpResponseRedirect(reverse('event-detail', args=(pk, event_id, )))

    simulator_address = os.environ['SIMULATOR_ADDRESS']
    url = simulator_address + 'simulate/'

    try:
        r = requests.get(simulator_address) # ping HiSTAV to check if it's online
        # Using pickle serializer to have the datetime objects not transformed to string : https://stackoverflow.com/questions/48811824/how-can-i-deserialize-a-datetime-string-in-celery/48812310
        result = simulate_task.apply_async(args=[url, pk, event.id, event.WritingPeriodicity, event.UpdateMaximumValue, event.WritingPeriodicityUnit, event.UpdateMaximumValueUnit, event.startDate, event.endDate, event.startTime, event.endTime], serializer='pickle')
        # # Combination hasSimulation = False + task_id = val means it's processing
        event.hasSimulation = False # Assume there is no simulation generated
        event.task_id = result.task_id
        event.requester = request.user
        event.save()
        messages.success(request, 'Simulation run request sent')
    except: # HiSTAV not online
        messages.error(request, 'Couldn\'t connect to HiSTAV')
    
    print("RUN SIMULATION")
    return HttpResponseRedirect(reverse('event-detail', args=(pk, event.id,)))

# # TODO: This is to be putted in a task
# def request_simulation(context, event_id, writing_perio, max_update_perio, writing_unit, update_unit, init_date, end_date, init_time, end_time): # function to request a simulation for a certain context
#     url = os.environ['SIMULATOR_ADDRESS'] + 'simulate/'

#     payload = {'context_name': context.Name,
#                 'event_id': event_id}

#     #prepare files

#     frequency_file = prepare_frequency_file(writing_perio, max_update_perio, writing_unit, update_unit)
#     time_file = prepare_time_file(init_date, end_date, init_time, end_time)
#     boundary_file = prepare_boundaries_file(context)

#     files = prepare_gauge_file(context, init_date, end_date, init_time, end_time)

#     files.append(('frequency', frequency_file))
#     files.append(('time', time_file))
#     files.append(('boundaries', boundary_file))

#     r = requests.post(url, files=files, params=payload)

#     return r

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

# TODO: this checks if the simulation generation has finished when the user is in the event main page
def inform_event_status(request, event_id): # Function to inform if event is generated
    event = e_ContextEvent.objects.get(id=event_id)
    if event.hasSimulation:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)


@login_required
def event_status_progress(request, event_id):
    event = get_object_or_404(e_ContextEvent, id=event_id)
    # get_object_or_404(Membership, organization=context.organization, user=request.user)
    simulator_address = os.environ['SIMULATOR_ADDRESS']
    url = simulator_address + 'simulate-status/'

    try:
        payload = {'event_id': event_id, 'context_name': event.context.Name}
        response = requests.get(url, params=payload)
        if response.status_code != 200:
            return HttpResponse(status=400)
        
        body = response.content.decode("utf-8")
        lastline = get_last_line(body)
        status = get_status(lastline)

        # Notification
        if ("Fail" in status) or ("Finished successfully" in status):
            notify.send(sender=event, recipient=event.requester, action_object=event.context.organization, verb=f"Event {event.Name} has finished its simulation with status '{status}'")

        return JsonResponse({'status' : status, 'message' : lastline, 'full_log' : body})
    except: # HiSTAV not online
        # 503 = service unavailable
        return HttpResponse(status=503)
    

def event_status_change(request, event_id): # Function to mark event has generated
    event = e_ContextEvent.objects.get(event_id)
    if request.GET.get('status'):
        event.hasSimulation = True
        event.task_id = None # task finished
    else:
        event.hasSimulation = False

    event.save()

    return HttpResponse(status=200)

@login_required
def event_progress(request, event_id):
    event = get_object_or_404(e_ContextEvent, id=event_id)
    # if not context_organization_edit_permission_check(request.user, e_context.organization): #verify that the user is logged in
    #     return HttpResponse('Unauthorized', status=401)

    event = {
        'event': event
    }
    
    return render(request, 'context/event_progress.html', event)

@login_required
def regenerate_event_confirm(request, event_id):
    event = get_object_or_404(e_ContextEvent, id=event_id)
    # if not context_organization_edit_permission_check(request.user, e_context.organization): #verify that the user is logged in
    #     return HttpResponse('Unauthorized', status=401)

    event = {
        'event': event
    }
    
    return render(request, 'context/regenerate_event_confirm.html', event)

