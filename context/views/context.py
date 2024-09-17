import os
import shutil
import zipfile
import geojson
import datetime

from rest_framework import viewsets
from io import BytesIO
from zipfile import ZipFile

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.core import serializers

from django.contrib import messages
from django_filters.views import FilterView

from django.db.models import Count, Case, When, Value 
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from rivercureproject import settings


from ..forms import ContextForm, UploadContextForm
from ..models import e_Context, e_ContextSensor, e_ContextEvent, ContextMembership
from ..serializers import ContextSerializer
from ..filters import ContextFilter, ContextSensorFilter

from .authorization import *
from .prepare_files import *
from .upload import boundaryline_creation

from rivercureproject.settings import MEDIA_ROOT
from rivercureportal.authorization import is_platform_admin
from sensors.models import Sensor
from challenges.models import e_Challenge, ChallengeState
from organization.models import Membership, Organization
from organization.authorization import belongs_to_organization
from context.forms import ContextDetailsForm, ContextInitialForm
from contributions.models import e_ContextContribution, ContributionStatus

from context.views.upload import alignment_creation, context_creation, refinement_creation
from context.views.helpers import get_context_folder_path, get_log_folder_path


class ContextUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_Context
    form_class = ContextDetailsForm
    context_object_name = 'context'
    template_name = 'context/context/form.html'
    pk_url_kwarg = 'contextCode'

    def get_success_url(self):
        return reverse('context-detail', args=(self.object.code,))

    def test_func(self):
        return context_organization_edit_permission_check(self.request.user, self.get_object().organization)


class ContextListView(LoginRequiredMixin, ListView):
    model = e_Context
    context_object_name = 'contexts'
    template_name = 'context/context/list.html'
    paginate_by = 10

    def get_queryset(self):
        organizationCode = self.request.session['organizationCode']
        if organizationCode:
            organization = get_object_or_404(Organization, code=organizationCode)
            context_list = e_Context.objects.filter(organization=organization)
        else:
            context_list = e_Context.objects.filter(creator=self.request.user)

        self.filter = ContextFilter(self.request.GET, queryset=context_list)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter
        context['permission_to_add'] = context_general_create_permission_check(self.request.user)
        return context


class PublicContextFilterView(FilterView):
    model = e_Context
    template_name = 'context/context/citizen_home2.html'
    filterset_class = ContextFilter
    context_object_name = 'public_contexts'

    def get_queryset(self):
        # context_list = e_Context.objects.exclude(isPublic=False).alias(nr_contributions=Count('e_contextcontribution')).order_by('-nr_contributions', 'code')

        # Order by number of Accepted contributions belonging to this Context (from higher to lower)
        # Ordering by code also because of repeating results (See https://stackoverflow.com/questions/5044464/django-pagination-is-repeating-results)
        acceptedContributions = Count("e_contextcontribution", filter=Q(e_contextcontribution__state=ContributionStatus.ACCEPTED))
        context_list = e_Context.objects.exclude(isPublic=False).annotate(acceptedContributions=acceptedContributions).order_by('-acceptedContributions', 'code')
        return context_list
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # List of all public contexts (for JS)
        public_contexts = e_Context.objects.exclude(isPublic=False)
        context['public_contexts_json'] = serializers.serialize('json', list(public_contexts), fields=('code', 'Name', 'description', 'geomExternalBoundary', 'CLExternalBoundary', 'picture'))

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
        context['belongsToOrg'] = belongs_to_organization(user, organization)

        return context

    def test_func(self, *args, **kwargs):
        context = self.get_object()
        return context.isPublic or Membership.objects.filter(user=self.request.user, organization=context.organization).exists()

class PublicContextDetailView(UserPassesTestMixin, DetailView):
    model = e_Context
    context_object_name = 'context'
    template_name = 'context/context/public_context_detail.html'
    pk_url_kwarg = 'contextCode'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['is_admin'] = is_platform_admin(self.request.user)
        # context['is_context_event_man'] = context_quiz_manager_check(self.request.user, self.get_object())

        context['contributions'] = e_ContextContribution.objects.filter(context=self.get_object().pk, state=ContributionStatus.ACCEPTED).order_by('-creationDateTime') # Contributions that belong to this context and are Accepted
        context['events'] = e_ContextEvent.objects.filter(context=self.get_object().pk) # Events that belong to this context
        # context['challenges'] = e_Challenge.objects.filter(context=self.get_object().pk, is_public=True, state=ChallengeState.PUBLISHED) # Public, published Challenges
        context['MEDIA_URL'] = settings.MEDIA_URL
        return context
    
    def test_func(self, *args, **kwargs):
        context = self.get_object()
        return context.isPublic


class ContextDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = e_Context
    context_object_name = 'context'
    pk_url_kwarg = 'contextCode'
    template_name = 'context/context/confirm_delete.html'
    success_url = reverse_lazy('context-list')

    def delete(self, *args, **kwargs):
        context: e_Context = self.get_object()
        context_folder = get_context_folder_path(context.tag)
        context_logs_folder = get_log_folder_path(context.tag)

        # Delete DTM and frictionCoef files
        path = os.path.join(MEDIA_ROOT, f'{context.Name}_dtm.tif')
        if os.path.exists(path):
            os.remove(path)

        path = os.path.join(MEDIA_ROOT, f'{context.Name}_dtm_optimized.tif')
        if os.path.exists(path):
            os.remove(path)

        path = os.path.join(MEDIA_ROOT, f'{context.Name}_frictionCoef.tif')
        if os.path.exists(path):
            os.remove(path)

        path = os.path.join(MEDIA_ROOT, f'{context.Name}_frictionCoef.tif')
        for i in os.listdir(MEDIA_ROOT):
            if os.path.isfile(os.path.join(MEDIA_ROOT, i)) and f'frictionCoef_{context.Name}' in i:
                os.remove(f'{MEDIA_ROOT}{i}')

        if os.path.exists(context_folder):
            shutil.rmtree(context_folder)

        if os.path.exists(context_logs_folder):
            shutil.rmtree(context_logs_folder)

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
        context_sensor_list = e_ContextSensor.objects.filter(
            boundary_point__contextBoundaryLine__context__code=self.context.code).distinct('sensor')
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
    context_sensors = context_sensors | Sensor.objects.filter(sensorClass__organization=e_Context.objects.get(
        pk=context_code).organization, sensorClass__organization__is_active=True)

    previous_context_sensors = set()
    for elem in e_ContextSensor.objects.filter(boundary_point__contextBoundaryLine__context=get_object_or_404(e_Context, pk=context_code)):
        previous_context_sensors.add(elem.sensor.pk)
    # Adds previously added sensors (from other organizations that are suspended) to the queryset
    context_sensors = context_sensors | Sensor.objects.filter(pk__in=previous_context_sensors)
    return context_sensors


@login_required
def manage_context(request, contextCode):
    context = get_object_or_404(e_Context, code=contextCode)
    web_host = os.environ['CONTEXT_API']

    context = {
        'sensors': get_context_sensors(contextCode),
        'form': ContextForm(),
        'api': f'http://{web_host}/contexts/api/context/',
        'context': context
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

                messages.success(request, f'Context updated with success!')

                return HttpResponseRedirect(reverse('context-detail', kwargs={'contextCode': e_context.code}))
            except Exception as e:
                print(f'Error saving context: {e}')
                messages.warning(request, f'Context update failed')

        else:
            messages.warning(request, f'Context info is not complete')
    else:
        context['context'] = e_Context.objects.get(code=contextCode)

    return render(request, 'context/context/manage.html', context)


class ContextViewSet(viewsets.ModelViewSet):
    queryset = e_Context.objects.all()
    lookup_field = 'code'
    serializer_class = ContextSerializer


@login_required
def download_context(request, contextCode):  # function that allows the download of an context
    # verify that the user is logged in
    if not context_organization_edit_permission_check(request.user, e_Context.objects.get(code=contextCode).organization):
        return HttpResponse('Unauthorized', status=401)

    message = None  # Message to send to user in case of failure
    # prepare geojson for download

    # Need to check if context code exists
    try:
        # ------------------ Domain --------------------------------
        domain_file = prepare_domain(contextCode)
        context_name = domain_file['name']
        # ------------------ Alignment --------------------------------
        alignment_file = prepare_alignment(contextCode, context_name)
        # ------------------ Refinement --------------------------------
        refinement_file = prepare_refinement(contextCode, context_name)
        # ------------------ Boundary --------------------------------
        boundary_file = prepare_boundaries(contextCode, context_name)
        # ------------------ Boundary Points --------------------------------
        boundary_point_file = prepare_boundary_points(contextCode, context_name)
        # endof json preparation

        mem_file = BytesIO()  # memory where the zip file will be created
        with ZipFile(mem_file, 'w') as zipFolder:  # create a zipped folder to return to the user
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
        messages.warning(request, f'Context not complete for download')
        print(f'Error downloading context: {e}')
        return redirect(request.META['HTTP_REFERER'])


@login_required
def preprocessing_results(request):  # function to redirect the user to the paraviewweb visualizer
    paraviewweb_visualizer_url = 'http://localhost:8090'
    return redirect(paraviewweb_visualizer_url)


def zip_file(file_name, file_path):
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as zip_file:
        zip_info = zipfile.ZipInfo(file_name)
        zip_info.compress_type = zipfile.ZIP_DEFLATED
        with open(file_path, 'rb') as fd:
            zip_file.writestr(zip_info, fd.read())
    buf.seek(0)
    return buf


@login_required
def download_preprocessing_results(request, contextCode):
    context = get_object_or_404(e_Context, code=contextCode)

    file_path = os.path.join(get_context_folder_path(context.tag), 'mesh', 'vtk', 'meshQuality.vtk')
    if not os.path.exists(file_path):
        messages.error(request, "File not found")
        return redirect('context-detail', contextCode=contextCode)

    buf = zip_file(f'{context.Name}_mesh.vtk', file_path)
    response = FileResponse(buf)
    response['Content-Disposition'] = f'attachment; filename="{context.Name}_mesh.zip"'

    return response
