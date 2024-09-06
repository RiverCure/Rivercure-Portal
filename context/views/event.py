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

from common.utils import is_mobile

from context.models import e_Context, e_ContextEvent, e_ContextEventResult
from context.forms import EventForm
from context.filters import EventFilter, QuizManagerFilter, QuizManagerAddFilter, EventChallengeListFilter
from context.tasks import simulate_task
from context.views.context import zip_file
from context.views.helpers import cancel_execution, cancel_task, copy_file_to_media_folder, get_context_folder_path, get_event_rasters_files
from context.views.mesh import Status, get_status, tail, check_celery

from sensors.models import Sensor
from notifications.signals import notify
from organization.authorization import belongs_to_organization
from challenges.models import e_Challenge, ChallengeState
from organization.authorization import is_org_quiz_manager

from ..filters import QuizManagerContextFilter, MyChallengesFilter

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

        # If user belongs to Org
        if belongs_to_organization(self.request.user, event.context.organization):
            # If Quiz Manager, see every Challenge of this Event
            if is_org_quiz_manager(self.request.user, event.context.organization):
                context['challenges'] = e_Challenge.objects.filter(event=event.id).order_by('-creation_datetime')
            else:
                # Else, show every Published Challenge of this event
                context['challenges'] = e_Challenge.objects.filter(event=event.id, state=ChallengeState.PUBLISHED).order_by('-creation_datetime')
        else:
            # Otherwise, only show Published Public Challenges
            context['challenges'] = e_Challenge.objects.filter(event=event.id, state=ChallengeState.PUBLISHED, is_public=True).order_by('-creation_datetime')
        context['isQuizMan'] = is_org_quiz_manager(self.request.user, event.context.organization)

        return context


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

        # If user belongs to Org
        if belongs_to_organization(self.request.user, event.context.organization):
            # If Quiz Manager, see every Challenge of this Event
            if is_org_quiz_manager(self.request.user, event.context.organization):
                challenge_list = e_Challenge.objects.filter(event=event_id).order_by('-creation_datetime')
            else:
                # Else, show every Published Challenge of this event
                challenge_list = e_Challenge.objects.filter(event=event_id, state=ChallengeState.PUBLISHED).order_by('-creation_datetime')
        else:
            # Otherwise, only show Published Public Challenges
            challenge_list = e_Challenge.objects.filter(event=event_id, state=ChallengeState.PUBLISHED, is_public=True).order_by('-creation_datetime')

        return challenge_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event_id = self.kwargs['event_id']

        context['event'] = e_ContextEvent.objects.get(pk=event_id)
        context['isQuizMan'] = is_org_quiz_manager(self.request.user, context['event'].context.organization)
        context['is_mobile'] = is_mobile(self.request)
        
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



# class QuizManagerContextsListView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
#     model = e_Context
#     template_name = 'context/quiz/quiz_manager_my_context_list.html'
#     context_object_name = 'contexts'
#     filterset_class = QuizManagerContextFilter
#     paginate_by = 6

#     def get_queryset(self):
#         # Get Contexts for which this user is a Quiz Manager
#         contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_quizManager')
#         return contexts

#     def get_context_data(self, **kwargs):
#         context = super(QuizManagerContextsListView, self).get_context_data(**kwargs)
#         # Filter
#         contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_quizManager')
#         context['filter'] = QuizManagerContextFilter(self.request.GET, queryset=contexts)

#         return context

#     def test_func(self):
#         # User must be a Quiz Manager (in some Context)
#         return general_quiz_manager_check(self.request.user)
    
    
# class QuizManagerChallengesFilterView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
#     model = e_Challenge
#     template_name = 'challenges/my_challenges_list.html'
#     filterset_class = MyChallengesFilter
#     context_object_name = 'challenges'
#     paginate_by = 9

#     def get_queryset(self):

#         # Show Challenges from this user's Contexts
#         user_contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_quizManager').values_list('context')
#         challenge_list = e_Challenge.objects.filter(created_by=self.request.user, event__context__in=user_contexts)

#         return challenge_list
    
#     def get_context_data(self, **kwargs):

#         context = super().get_context_data(**kwargs)
        
#         user_contexts = user_contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_quizManager').values_list('context')
#         context['challenge_list'] = e_Challenge.objects.filter(created_by=self.request.user, event__context__in=user_contexts)
#         context['filter'] = MyChallengesFilter(self.request.GET, queryset=context['challenge_list'])
        
#         return context

#     def test_func(self):
#         # Only Quiz Manager gets access to this page
#         return general_quiz_manager_check(self.request.user)