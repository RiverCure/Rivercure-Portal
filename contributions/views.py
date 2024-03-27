from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, DetailView, DeleteView
from django.contrib.gis.geos import Point
from django_filters.views import FilterView
from django.http import HttpResponseRedirect, Http404
from django.contrib import messages

import datetime

from .models import e_ContextContribution, e_ContributionAttachment, ContributionStatus
from .forms import ContributionInitialForm, RejectionForm
from .filters import ContributionFilter, MyContributionsFilter
from .authorization import *
from context.models import e_Context
from context.views.authorization import context_organization_edit_permission_check, context_moderator_check
from rivercureproject import settings



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
        new_contribution.creationDateTime = datetime.datetime.now()
        new_contribution.observationPlace = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])

        # Save
        new_contribution.save()

        # Deal with files
        files = form.cleaned_data["file_field"]
        for f in files:
            handle_uploaded_file(new_contribution, f)
        
        # Send success message (to be shown in detail page)
        messages.success(self.request, 'Thank you for submitting your Contribution! Your participation is very valuable to the RiverCure Portal.')

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
        contribution_list = e_ContextContribution.objects.filter(context=context_code, state=ContributionStatus.ACCEPTED) # Only show Accepted Contributions

        return contribution_list
    
    def get_context_data(self, **kwargs):
        context_code = self.kwargs['contextCode']

        context = super().get_context_data(**kwargs)
        context['context'] = get_object_or_404(e_Context, code=context_code)
        context['contribution_list'] = e_ContextContribution.objects.filter(context=context_code, state=ContributionStatus.ACCEPTED) # Only show Accepted Contributions
        context['filter'] = ContributionFilter(self.request.GET, queryset=context['contribution_list'])
        
        return context



class ContributionDetailView(DetailView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_detail.html'
    pk_url_kwarg = 'contributionId'
    context_object_name = 'contribution'

    # We override this method because we want to control who gets to see this page
    # As seen in: https://stackoverflow.com/a/42653231/12387341
    def get_object(self, queryset=None):
        contribution = super().get_object(queryset)

        # If Contribution is PENDING or REJECTED
        if contribution.state != ContributionStatus.ACCEPTED:
            # And if user is not author OR moderator OR context manager OR org manager (of the contribution's context and organization)
            if not (author_of_contribution_check(self.request.user, contribution) or context_moderator_check(self.request.user, contribution.context) or context_organization_edit_permission_check(self.request.user, contribution.context.organization)):
                # Then the user should not get access to the page
                raise Http404()
        
        # Otherwise (Contribution is ACCEPTED or user has correct permissions) then just show it
        return contribution
                

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        org = self.get_object().context.organization

        context['contribution_media_list'] = e_ContributionAttachment.objects.filter(contribution=self.get_object().pk)
        context['MEDIA_URL'] = settings.MEDIA_URL
        context['isContextOrOrgManager'] = context_organization_edit_permission_check(user, org) # TODO: Best way to do this?
        context['isMod'] = context_moderator_check(self.request.user, self.get_object().context.code)
        context['form'] = RejectionForm()
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



class ContributionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_confirm_delete.html'
    pk_url_kwarg = 'contributionId'
    success_url = reverse_lazy('my-contributions')
    context_object_name = 'contribution'

    def test_func(self):
        # Author is the only user who can delete the Contribution
        return author_of_contribution_check(self.request.user, self.get_object())


@login_required
def contributionAccept(request, contributionId):
    contribution = get_object_or_404(e_ContextContribution, pk=contributionId)

    # Make sure only (Context) Moderator can do this
    if not context_moderator_check(request.user, contribution.context):
        return HttpResponseRedirect(reverse('contribution-detail', args=[contributionId]))
    
    # Change Contribution state to ACCEPTED
    if contribution:
        contribution.accept()
        contribution.validatedBy = request.user
        contribution.validationDateTime = datetime.datetime.now()

        contribution.save()
    
        # TODO: Send notifs

    return redirect('contribution-detail', contributionId)

@login_required
def contributionReject(request, contributionId):
    contribution = get_object_or_404(e_ContextContribution, pk=contributionId)

    # Make sure only (Context) Moderator can do this
    if not context_moderator_check(request.user, contribution.context):
        return HttpResponseRedirect(reverse('contribution-detail', args=[contributionId]))
    
    # create a form instance and populate it with data from the request:
    form = RejectionForm(request.POST)

    if form.is_valid():
        # Save rejection reason in Contribution
        contribution.reject()
        contribution.rejectionReason = form.cleaned_data['rejectionReason']
        contribution.validatedBy = request.user
        contribution.validationDateTime = datetime.datetime.now()
        contribution.save()
        
        # TODO: Send notifs
        
        return HttpResponseRedirect(reverse('contribution-detail', args=[contributionId]))
    
    return redirect('contribution-detail', contributionId)


# Helper functions
def handle_uploaded_file(contribution, uploaded_file):
    attachment = e_ContributionAttachment.objects.create(file=uploaded_file, contribution=contribution)

    attachment.save()