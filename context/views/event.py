from django.shortcuts import get_object_or_404, redirect, render
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django_filters.views import FilterView

from context.models import e_Context, e_ContextEvent, e_ContextEventResult
from context.forms import EventForm
from context.filters import EventFilter, EventManagerFilter, EventManagerAddFilter, EventChallengeListFilter
from context.tasks import simulate_task
from context.views.context import zip_file
from context.views.helpers import cancel_execution, cancel_task, copy_file_to_media_folder, get_context_folder_path, get_event_rasters_files
from context.views.mesh import Status, get_status, tail, check_celery

from sensors.models import Sensor
from notifications.signals import notify
from organization.authorization import belongs_to_organization
from challenges.models import e_Challenge, ChallengeState

from ..filters import EventManagerContextFilter, MyContextsChallengesFilter

from .authorization import *
from .prepare_files import *
from rivercureproject import settings

import os
import requests
from io import BytesIO
from zipfile import ZipFile
import json


class ContextEventListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    context_object_name = 'events'
    template_name = 'context/event/list.html'
    paginate_by = 15

    def setup(self, request, *args, **kwargs):
        self.context = get_object_or_404(e_Context, pk=kwargs['contextCode'])
        self.queryset = e_ContextEvent.objects.filter(context=self.context).order_by('id')
        return super().setup(request, *args, **kwargs)

    def get_queryset(self):
        self.filter = EventFilter(self.request.GET, queryset=self.queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super(ContextEventListView, self).get_context_data(**kwargs)
        context['hasPerm'] = context_organization_event_permission_check(self.request.user, self.context.organization)
        context['context'] = self.context
        context['filter'] = self.filter

        return context

    def test_func(self):
        return self.context.isPublic or belongs_to_organization(self.request.user, self.context.organization)


class EventDetailView(LoginRequiredMixin, DetailView):
    model = e_ContextEvent
    context_object_name = 'event'
    pk_url_kwarg = 'event_id'
    template_name = 'context/event/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        context['hasPerm'] = context_organization_event_permission_check(
            self.request.user, event.context.organization)

        rasters = get_event_rasters_files(event.context.tag)
        for key in rasters.keys():
            file_name = f'{event.Name}_{key}.tif'
            path = os.path.join(settings.MEDIA_ROOT, file_name)
            if os.path.isfile(path):
                rasters[key] = os.path.join(os.sep, settings.MEDIA_URL, file_name)
            else:
                rasters[key] = None

        context['rasters'] = json.dumps(rasters, cls=DjangoJSONEncoder)

        # Challenges
        is_user_in_org = context_organization_belong_check(self.request.user, event.context.organization)
        if is_user_in_org:
            # Then show every Challenge of this event
            context['challenges'] = e_Challenge.objects.filter(event=event.id, state=ChallengeState.PUBLISHED).order_by('-creation_datetime') # Only show published Challenges
        else:
            # Otherwise, only show Public Challenges
            context['challenges'] = e_Challenge.objects.filter(event=event.id, state=ChallengeState.PUBLISHED, is_public=True).order_by('-creation_datetime') # Only show published Challenges
        # context['challenges'] = e_Challenge.objects.filter(event=event.id, state=ChallengeState.PUBLISHED).order_by('-creation_datetime') # Only show published Challenges
        context['isEventManager'] = context_event_manager_check(self.request.user, event.context)

        return context


# TODO: See if this is working
class EventChallengesFilterView(LoginRequiredMixin, FilterView):
    model = e_Challenge
    template_name = 'context/event/challenge_list.html'
    filterset_class = EventChallengeListFilter
    pk_url_kwarg = 'event_id'
    context_object_name = 'challenges'
    paginate_by = 9

    def get_queryset(self):

        event_id = self.kwargs['event_id']
        event = e_ContextEvent.objects.get(pk=event_id)

        is_user_in_org = context_organization_belong_check(self.request.user, event.context.organization)
        if is_user_in_org:
            # Then show every Challenge of this event
            challenge_list = e_Challenge.objects.filter(event=event_id, state=ChallengeState.PUBLISHED).order_by('-creation_datetime') # Only show published Challenges
        else:
            # Otherwise, only show Public Challenges
            challenge_list = e_Challenge.objects.filter(event=event_id, state=ChallengeState.PUBLISHED, is_public=True).order_by('-creation_datetime') # Only show published Challenges
        # challenge_list = e_Challenge.objects.filter(event=event_id, state=ChallengeState.PUBLISHED)

        return challenge_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event_id = self.kwargs['event_id']

        context['event'] = e_ContextEvent.objects.get(pk=event_id)

        is_user_in_org = context_organization_belong_check(self.request.user, context['event'].context.organization)
        if is_user_in_org:
            # Then show every Challenge of this event
            context['challenge_list'] = e_Challenge.objects.filter(event=event_id, state=ChallengeState.PUBLISHED).order_by('-creation_datetime') # Only show published Challenges
        else:
            # Otherwise, only show Public Challenges
            context['challenge_list'] = e_Challenge.objects.filter(event=event_id, state=ChallengeState.PUBLISHED, is_public=True).order_by('-creation_datetime') # Only show published Challenges
        # context['challenge_list'] = e_Challenge.objects.filter(event=event_id, state=ChallengeState.PUBLISHED)
        context['filter'] = EventChallengeListFilter(self.request.GET, queryset=context['challenge_list'])
        
        return context


@login_required
def view_events_results(request, event_id):  # function to view the results of an event simulation
    event = e_ContextEvent.objects.get(pk=event_id)
    web_host = os.environ['CONTEXT_API']

    context = {
        'api': f'http://{web_host}/contexts/api/context/',
        'context': event.context,
        'sensors': Sensor.objects.all(),
        'event': event,
        'max_depth': event.context_event_results.max_depth.id,
        'max_level': event.context_event_results.max_level.id,
        'max_q': event.context_event_results.max_q.id,
        'max_vel': event.context_event_results.max_vel.id
    }

    return render(request, 'context/event/results.html', context)


@login_required
def download_simulation_results(request, event_id):  # function to download simulation results
    event = get_object_or_404(e_ContextEvent, pk=event_id)
    context = event.context

    folder_path = os.path.join(get_context_folder_path(context.tag), 'output', 'maxima')
    if not os.path.exists(folder_path) or len(os.listdir(folder_path)) == 0:
        messages.error(request, "File not found")
        return HttpResponseRedirect(reverse('event-detail', args=(context.code, event.id,)))

    file_name = os.listdir(folder_path)[0]
    filepath = os.path.join(folder_path, file_name)
    buf = zip_file(file_name, filepath)

    response = FileResponse(buf)
    response['Content-Disposition'] = f'attachment; filename="{context.code}_{event.Name}_simulation_results.zip"'

    return response


def handle_simulation_results(request, event_id):  # function to handle simulation results
    sim_url = os.environ['SIMULATOR_ADDRESS']

    event = e_ContextEvent.objects.get(pk=event_id)
    event.hasSimulation = True
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


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = e_ContextEvent
    template_name = 'context/event/form.html'
    form_class = EventForm
    context_object_name = 'event'

    def dispatch(self, request, *args, **kwargs):
        context = get_object_or_404(e_Context, pk=self.kwargs['pk'])
        self.context = context
        # if context.e_contextevent_set.count() >= 1:
        #     messages.error(
        #         request, 'There already exists an event for this context. Currently, RiverCure only allows one event per context.')
        #     return redirect('event-list', contextCode=context.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['context'] = self.context
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

        return HttpResponseRedirect(reverse('event-detail', args=(context.code, obj.id,)))

    def test_func(self):
        organization = e_Context.objects.get(pk=self.kwargs['pk']).organization
        return context_organization_event_permission_check(self.request.user, organization)


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_ContextEvent
    template_name = 'context/event/form.html'
    form_class = EventForm
    pk_url_kwarg = 'event_id'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['context'] = get_object_or_404(e_Context, pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse('event-list', args=(self.get_object().context.code, ))

    def test_func(self):
        return context_organization_event_permission_check(self.request.user, self.get_object().context.organization)

# TODO: Change to FilterView
class ContextEventManagersListView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
    model = User
    template_name = 'context/event/event_manager_list.html'
    context_object_name = 'users'
    ordering = ['first_name', 'last_name'] # TODO: Change to something else?
    pk_url_kwarg = 'contextCode'
    filterset_class = EventManagerFilter
    paginate_by = 5

    def get_queryset(self):
        _context = e_Context.objects.get(pk=self.kwargs['contextCode'])
        members = ContextMembership.objects.filter(context=_context, permission='context_eventManager')

        return members

    def get_context_data(self, **kwargs):
        context_code = self.kwargs['contextCode']
        _context = e_Context.objects.get(pk=context_code)

        context = super(ContextEventManagersListView, self).get_context_data(**kwargs)
        context['context'] = _context
        context['canEdit'] = context_organization_edit_permission_check(self.request.user, _context.organization) # Only Org or Context Managers can edit Moderators of a Context
        members = ContextMembership.objects.filter(context=context_code, permission='context_eventManager')
        context['filter'] = EventManagerFilter(self.request.GET, queryset=members)
        return context

    # Only users who belong to this Organization can see this
    def test_func(self):
        _context = e_Context.objects.get(pk=self.kwargs['contextCode'])
        return belongs_to_organization(self.request.user, _context.organization)


class ContextEventManagerAddListView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
    model = User
    template_name = 'context/event/event_manager_add_list.html'
    context_object_name = 'users'
    ordering = ['first_name', 'last_name'] # TODO: Working?
    pk_url_kwarg = 'contextCode' # = self.kwargs['contextCode']
    filterset_class = EventManagerAddFilter
    paginate_by = 5

    def get_queryset(self):
        _context = e_Context.objects.get(pk=self.kwargs['contextCode']) # TODO: Change these _context to just self.kwargs['contextCode'] when possible

        # Only show organization members that are not already event managers for that context
        event_managers = ContextMembership.objects.filter(context=_context, permission='context_eventManager').values('user')
        members = Membership.objects.filter(organization=_context.organization, permission='org_member').exclude(user__in=event_managers)

        return members

    def get_context_data(self, **kwargs):
        _context = e_Context.objects.get(pk=self.kwargs['contextCode'])

        context = super(ContextEventManagerAddListView, self).get_context_data(**kwargs)
        context['context'] =  _context

        # Only show organization members that are not already event managers for that context
        event_managers = ContextMembership.objects.filter(context=_context, permission='context_eventManager').values('user')
        org_members = Membership.objects.filter(organization=_context.organization, permission='org_member').exclude(user__in=event_managers)
        # Filter
        context['filter'] = EventManagerAddFilter(self.request.GET, queryset=org_members)

        return context

    def test_func(self):
        _context = e_Context.objects.get(pk=self.kwargs['contextCode'])
        return context_organization_edit_permission_check(self.request.user, _context.organization)

@login_required
def contextEventManagerAdd(request, contextCode, userId):
    _context = get_object_or_404(e_Context, pk=contextCode)
    user = get_object_or_404(User, pk=userId)
    organization = _context.organization

    # Make sure only Organization Manager and Context Manager can do this
    # And that the user belongs to the Org
    if not context_organization_edit_permission_check(request.user, organization.id) or not context_organization_belong_check(user, organization): # TODO: Is this working? # TODO: Substitute context_organization_belong_check with belongs_to_organization from organization/authorization.py !!!
        return HttpResponseRedirect(reverse('event-manager-list', args=[contextCode]))
    
    # Make sure user is not already an Event Manager
    if context_event_manager_check(user, _context):
        return HttpResponseRedirect(reverse('event-manager-list', args=[contextCode]))
    
    if user and _context:
        member = ContextMembership(user=user, context=_context, permission='context_eventManager')
        member.save()

        # TODO: Send notifs

    return redirect('event-manager-list', contextCode)

@login_required
def contextEventManagerRemove(request, contextCode, userId):
    _context = get_object_or_404(e_Context, pk=contextCode)

    # Make sure only Organization Manager and Context Manager can do this
    if not context_organization_edit_permission_check(request.user, _context.organization.id):
        return HttpResponseRedirect(reverse('event-manager-list', args=[contextCode]))
    
    user = get_object_or_404(User, pk=userId)
    context_membership_user = get_object_or_404(ContextMembership, user=user, context=_context, permission='context_eventManager')

    if context_membership_user:
        context_membership_user.delete()

        # TODO: Send notifs
    
    return redirect('event-manager-list', contextCode)


def request_simulation(request, pk, event_id):
    event = get_object_or_404(e_ContextEvent, id=event_id)
    if not context_organization_event_permission_check(request.user, event.context.organization):
        return HttpResponseRedirect(reverse('event-detail', args=(pk, event_id, )))

    if check_celery():
        task = simulate_task.delay(event_id)
        # # Combination hasSimulation = False + task_id = val means it's processing
        event.hasSimulation = False  # Assume there is no simulation generated
        event.task_id = task.task_id
        event.requester = request.user
        event.save()
        messages.success(request, 'Simulation run request sent')
    else:  # HiSTAV not online
        messages.error(request, 'Background process offline: Contact admin.')

    return redirect('event-detail', pk=pk, event_id=event.id)


@login_required
def event_progress(request, event_id):
    '''Renders the page that shows the progress of the event simulation'''
    event = get_object_or_404(e_ContextEvent, id=event_id)
    return render(request, 'context/event/progress.html', {'event': event})


@login_required
def event_status_progress(request, event_id):
    event = get_object_or_404(e_ContextEvent, id=event_id)

    log_file = os.path.join('logs', event.context.tag, f'{event.Name}_simulation_log.txt')
    if not os.path.isfile(log_file):
        return HttpResponse(status=404)

    with open(log_file, "r") as f_log:
        tail_list = tail(f_log, 50)

    tail_log = ''.join(tail_list)
    lastline = tail_list[-1]
    status = get_status(lastline)

    if status == Status.FINISH:
        event.hasSimulation = True
        event.task_id = None
        event.proc_id = None
        event.save()

        notify.send(sender=event, recipient=event.requester, action_object=event.context.organization,
                    verb=f"Simulation of event {event.Name} has finished successfully")
    elif status == Status.FAIL:
        notify.send(sender=event, recipient=event.requester, action_object=event.context.organization,
                    verb=f"Simulation of event {event.Name} has failed")

    return JsonResponse({'status': status.value, 'message': lastline, 'full_log': tail_log})


@login_required
def regenerate_event_confirm(request, event_id):
    event = get_object_or_404(e_ContextEvent, id=event_id)
    return render(request, 'context/event/regenerate_event_confirm.html', {'event': event})


@login_required
def cancel_event_confirm(request, event_id):
    event = get_object_or_404(e_ContextEvent, id=event_id)
    return render(request, 'context/event/cancel_event_confirm.html', {'event': event})


def inform_event_status(request, event_id):
    '''Called repeatedly by the frontend when in /contexts/event-status/<int:contextId> to check if the event has simulated'''
    event = e_ContextEvent.objects.get(id=event_id)
    if event.hasSimulation:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)


def cancel_simulation(request, pk, event_id):
    event = get_object_or_404(e_ContextEvent, id=event_id)
    if not context_organization_event_permission_check(request.user, event.context.organization):
        return HttpResponseRedirect(reverse('event-detail', args=(pk, event_id, )))

    try:
        if event.proc_id:
            cancel_execution(event)
        if event.task_id:
            cancel_task(event)
    except:
        event.proc_id = None
        event.task_id = None
        event.save()

    messages.success(request, 'Simulation stopped successfully')

    return redirect('event-detail', pk=pk, event_id=event.id)



class EventManagerContextsListView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
    model = e_Context
    template_name = 'context/event/event_manager_my_context_list.html'
    context_object_name = 'contexts'
    filterset_class = EventManagerContextFilter
    paginate_by = 6

    def get_queryset(self):
        # Get Contexts for which this user is an Event Manager
        contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_eventManager')
        return contexts

    def get_context_data(self, **kwargs):
        context = super(EventManagerContextsListView, self).get_context_data(**kwargs)
        # Filter
        contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_eventManager')
        context['filter'] = EventManagerContextFilter(self.request.GET, queryset=contexts)

        return context

    def test_func(self):
        # User must be an Event Manager (in some Context)
        return general_event_manager_check(self.request.user)
    
    
class MyContextsChallengesFilterView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
    model = e_Challenge
    template_name = 'challenges/my_challenges_list.html'
    filterset_class = MyContextsChallengesFilter
    context_object_name = 'challenges'
    paginate_by = 9

    def get_queryset(self):

        # Show Challenges from this user's Contexts
        user_contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_eventManager').values_list('context')
        challenge_list = e_Challenge.objects.filter(created_by=self.request.user, context__in=user_contexts)

        return challenge_list
    
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        
        user_contexts = user_contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_eventManager').values_list('context')
        context['challenge_list'] = e_Challenge.objects.filter(created_by=self.request.user, context__in=user_contexts)
        context['filter'] = MyContextsChallengesFilter(self.request.GET, queryset=context['challenge_list'])
        
        return context

    def test_func(self):
        # Only Event Manager gets access to this page
        return general_event_manager_check(self.request.user)