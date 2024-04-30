from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView, DeleteView
from django_filters.views import FilterView

from .models import e_Challenge

from context.models import e_ContextEvent


# TODO: Change to FilterView
class ChallengesListView(ListView):
    model = e_Challenge
    template_name = 'challenges/challenge_list.html'
    # filterset_class = ContributionFilter
    pk_url_kwarg = 'event_id'
    context_object_name = 'challenges'
    # paginate_by = 9

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event_id = self.kwargs['event_id']

        context['event'] = e_ContextEvent.objects.get(pk=event_id)
        
        return context