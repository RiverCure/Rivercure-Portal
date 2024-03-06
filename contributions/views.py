from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from datetime import datetime

from .models import e_ContextContribution,  e_ContributionAttachment
from .forms import ContributionInitialForm
from context.models import e_Context

# Create your views here.

class AllContributionsListView(LoginRequiredMixin, ListView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_list.html'

class ContributionCreateView(LoginRequiredMixin, CreateView):
    model = e_ContextContribution
    form_class = ContributionInitialForm
    template_name = 'contributions/contribution_form.html'
    context_object_name = 'contribution'
    # TODO: Change sucess_url to the new Contribution's page
    success_url = reverse_lazy('all-contributions-list') # We are overriding the get_absolute_url function of the e_ContextContribution model (if it had been defined)
    pk_url_kwarg = 'contextCode'

    def get_context_data(self, **kwargs):
        context_code = self.kwargs['contextCode']

        context = super().get_context_data(**kwargs)
        context['context_name'] = get_object_or_404(e_Context, code=context_code).Name
        
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
        _context = get_object_or_404(e_Context, code=context_code)
        new_contribution.context = _context # TODO: Check whether this is correct (aka if it shouldn't be the pk)
        new_contribution.creationDateTime = datetime.now()

        # Deal with files
        files = form.cleaned_data["file_field"]
        for f in files:
            print("hello file")
            # TODO: Create file object in DB
            attachment = e_ContributionAttachment(file=f, contribution=new_contribution.pk) # TODO: How to get contribution id?
            attachment.save() # TODO: Is it saving?
        
        # Save
        new_contribution.save()

        return super().form_valid(form)

class ContributionListView(ListView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_list.html'
    pk_url_kwarg = 'contextCode'
    context_object_name = 'contributions'
    # paginate_by = 10

    def get_queryset(self):

        context_code = self.kwargs['contextCode']
        context_list = e_ContextContribution.objects.filter(context=context_code)

        # TODO: Add Filter

        return context_list
    
    def get_context_data(self, **kwargs):
        context_code = self.kwargs['contextCode']

        context = super().get_context_data(**kwargs)
        context['context_name'] = get_object_or_404(e_Context, code=context_code).Name
        
        return context

class ContributionDetailView(DetailView):
    model = e_ContextContribution
    context_object_name = 'contribution'
    template_name = 'contributions/contribution_detail.html'
    pk_url_kwarg = 'contributionId'