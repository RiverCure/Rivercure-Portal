from django.urls import reverse
from django.contrib import messages
from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView, DeleteView
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin

from context.models import e_ContextEvent

from .models import e_Challenge
from .forms import ChallengeInitialForm


# TODO: Change to FilterView
class EventChallengesListView(ListView):
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


class ChallengeCreateView(LoginRequiredMixin, CreateView):
    model = e_Challenge
    form_class = ChallengeInitialForm
    template_name = 'challenges/challenge_form.html'
    context_object_name = 'challenge'
    pk_url_kwarg = 'event_id'

    # TODO: Uncomment this
    # def get_success_url(self):
    #     return reverse('challenge-detail', args=(self.object.id, ))

    def get_context_data(self, **kwargs):
        event_id = self.kwargs['event_id']

        context = super().get_context_data(**kwargs)

        context['event'] = e_ContextEvent.objects.get(pk=event_id)
        
        return context

    def form_invalid(self, form):
        messages.error(self.request, 'There is an error in the submission form. Please check what field(s) need to be adjusted.')
        return super().form_invalid(form)
    
    def form_valid(self, form):

        event = e_ContextEvent.objects.get(pk=self.kwargs['event_id'])

        new_challenge = form.save(commit=False)

        # Set metadata
        new_challenge.created_by = self.request.user
        new_challenge.event = event

        new_challenge.save()

        # Send success message (to be shown in Challenge detail page)
        messages.success(self.request, 'Your Challenge has been created successfully.')

        # TODO: Send confirmation email to user

        return super().form_valid(form)