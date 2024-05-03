from django.urls import reverse
from django.http import Http404, HttpResponse
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.views.generic import ListView, CreateView, DetailView, DeleteView, UpdateView
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from rivercureportal.authorization import is_platform_admin
from context.models import e_ContextEvent
from context.views.authorization import context_organization_edit_permission_check, context_event_manager_check

from .models import e_Challenge, ChallengeState
from .forms import ChallengeInitialForm


class ChallengeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = e_Challenge
    form_class = ChallengeInitialForm
    template_name = 'challenges/challenge_form.html'
    context_object_name = 'challenge'
    pk_url_kwarg = 'event_id'

    def test_func(self):
        # Only Event Manager or Platform Admin can do this
        return context_event_manager_check(self.request.user, self.get_object().event.context) or is_platform_admin(self.request.user)

    def get_success_url(self):
        return reverse('challenge-detail', args=(self.object.id, ))

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

class ChallengeDetailView(LoginRequiredMixin, DetailView):
    model = e_Challenge
    template_name = 'challenges/challenge_detail.html'
    pk_url_kwarg = 'challenge_id'
    context_object_name = 'challenge'

    # We override this method because we want to control who gets to see this page
    def get_object(self, queryset=None):
        challenge = super().get_object(queryset)

        # If Challenge is not PUBLISHED
        if challenge.state != ChallengeState.PUBLISHED:
            # And if user is not Event Manager of this Context, or a Context Manager or Org Manager of this Organization, or a Platform Admin
            if not (context_event_manager_check(self.request.user, challenge.event.context) or context_organization_edit_permission_check(self.request.user, challenge.event.context.organization) or is_platform_admin(self.request.user)):
                # The user does not have access to the page
                raise Http404()

        # Otherwise (Challenge is PUBLISHED or user has correct permission), user has access to page
        return challenge
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        challenge = e_Challenge.objects.get(pk=self.kwargs['challenge_id'])

        # canManage = user is Event Manager or Platform Admin
        context['canManage'] = context_event_manager_check(self.request.user, challenge.event.context) or is_platform_admin(self.request.user)

        return context

class ChallengeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = e_Challenge
    template_name = 'challenges/challenge_confirm_delete.html'
    context_object_name = 'challenge'
    pk_url_kwarg = 'challenge_id'

    def test_func(self):
        # Only Event Manager or Platform Admin can do this
        return context_event_manager_check(self.request.user, self.get_object().event.context) or is_platform_admin(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, "The Challenge was deleted successfully.")
        return super(ChallengeDeleteView,self).form_valid(form)
    
    
    def get_success_url(self):
        return reverse('event-challenge-list', args=(self.object.event.id, ))


# class ChallengeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
#     model = e_Challenge




    # model = e_Context
    # form_class = ContextDetailsForm
    # context_object_name = 'context'
    # template_name = 'context/context/form.html'
    # pk_url_kwarg = 'contextCode'

    # def get_success_url(self):
    #     return reverse('context-detail', args=(self.object.code,))

    # def test_func(self):
    #     return context_organization_edit_permission_check(self.request.user, self.get_object().organization)