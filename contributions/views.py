from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse
from django.contrib.gis.geos import Point
from django_filters.views import FilterView

from datetime import datetime

from .models import e_ContextContribution, e_ContributionAttachment
from .forms import ContributionInitialForm
from context.models import e_Context
from context.views.authorization import context_organization_edit_permission_check
from rivercureproject import settings
from .filters import ContributionFilter, MyContributionsFilter



class AllContributionsListView(LoginRequiredMixin, ListView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_list.html'



class ContributionCreateView(LoginRequiredMixin, CreateView):
    model = e_ContextContribution
    form_class = ContributionInitialForm
    template_name = 'contributions/contribution_form.html'
    context_object_name = 'contribution'
    pk_url_kwarg = 'contextCode'

    def get_success_url(self):
        return reverse('contribution-detail', args=(self.object.id, ))

    def get_context_data(self, **kwargs):
        context_code = self.kwargs['contextCode']

        context = super().get_context_data(**kwargs)
        context['context'] = get_object_or_404(e_Context, code=context_code)
        context['context_code'] = self.kwargs['contextCode']
        
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # Set metadata
        new_contribution = form.save(commit=False)

        new_contribution.createdBy = self.request.user
        context_code = self.kwargs['contextCode']
        _context = e_Context.objects.get(code=context_code)
        new_contribution.context = _context
        new_contribution.creationDateTime = datetime.now()
        new_contribution.observationPlace = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])

        # Save
        new_contribution.save()

        # Deal with files
        files = form.cleaned_data["file_field"]
        for f in files:
            handle_uploaded_file(new_contribution, f)

        return super().form_valid(form)



class ContributionListView(FilterView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_list.html'
    filterset_class = ContributionFilter
    pk_url_kwarg = 'contextCode'
    context_object_name = 'contributions'
    paginate_by = 9

    def get_queryset(self):

        context_code = self.kwargs['contextCode']
        contribution_list = e_ContextContribution.objects.filter(context=context_code)

        return contribution_list
    
    def get_context_data(self, **kwargs):
        context_code = self.kwargs['contextCode']

        context = super().get_context_data(**kwargs)
        context['context'] = get_object_or_404(e_Context, code=context_code)
        context['contribution_list'] = e_ContextContribution.objects.filter(context=context_code)
        context['filter'] = ContributionFilter(self.request.GET, queryset=context['contribution_list'])
        
        return context



class ContributionDetailView(DetailView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_detail.html'
    pk_url_kwarg = 'contributionId'
    context_object_name = 'contribution'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        org = self.get_object().context.organization

        context['contribution_media_list'] = e_ContributionAttachment.objects.filter(contribution=self.get_object().pk)
        context['MEDIA_URL'] = settings.MEDIA_URL
        context['isContextOrOrgManager'] = context_organization_edit_permission_check(user, org) # TODO: Best way to do this?
        return context



class MyContributionsListView(LoginRequiredMixin, FilterView):
    model = e_ContextContribution
    template_name = 'contributions/my_contributions_list.html'
    context_object_name = 'contributions'
    filterset_class = MyContributionsFilter
    paginate_by = 9

    def get_queryset(self):

        user = self.request.user

        contribution_list = e_ContextContribution.objects.filter(createdBy=user)

        return contribution_list
    
    def get_context_data(self, **kwargs):
        user = self.request.user

        context = super().get_context_data(**kwargs)
        context['contribution_list'] = e_ContextContribution.objects.filter(createdBy=user)
        context['filter'] = MyContributionsFilter(self.request.GET, queryset=context['contribution_list'])
        
        return context



# Helper functions
def handle_uploaded_file(contribution, uploaded_file):
    attachment = e_ContributionAttachment.objects.create(file=uploaded_file, contribution=contribution)

    attachment.save()