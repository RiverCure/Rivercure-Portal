from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from datetime import datetime

from .models import e_ContextContribution
from .forms import ContributionInitialForm

# Create your views here.

class ContributionListView(ListView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_list.html'

class ContributionCreateView(LoginRequiredMixin, CreateView):
    model = e_ContextContribution
    form_class = ContributionInitialForm
    context_object_name = 'contribution'
    template_name = 'contributions/contribution_form.html'
    success_url = reverse_lazy('contribution-list')

    # fields = ['observationDateTime', 'observationDescription', 'situationObserved']

    # def get_form_kwargs(self):
    #     kwargs = super(ContributionCreateView, self).get_form_kwargs()
    #     kwargs.update({'user_id': self.request.user.id})
    #     return kwargs

    # def form_valid(self, form):
    #     currentTime = datetime.datetime.now()
    #     organization = form.save(commit=False)
    #     # Add metadata to organization
    #     organization.creator = self.request.user
    #     organization.create_date = currentTime
    #     organization.save()

    #     return super().form_valid(form)

    def form_valid(self, form):
        # Set metadata
        new_contribution = form.save(commit=False)

        new_contribution.createdBy = self.request.user
        context = form.cleaned_data['context']
        new_contribution.context = context
        new_contribution.creationDateTime = datetime.now()
        
        new_contribution.save()

        return super().form_valid(form)