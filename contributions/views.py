from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from datetime import datetime

from .models import e_ContextContribution,  e_ContributionAttachment
from .forms import ContributionInitialForm

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
        context = form.cleaned_data['context']
        new_contribution.context = context
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
    paginate_by = 10