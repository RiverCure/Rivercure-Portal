from django.urls import reverse, reverse_lazy
from django.http import Http404, HttpResponse
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django_filters.views import FilterView

from django.views.generic import ListView, CreateView, DetailView, DeleteView, UpdateView

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from context.models import e_ContextEvent
from context.models import ContextMembership
from organization.models import Membership
from rivercureportal.authorization import is_platform_admin

from context.views.authorization import context_organization_edit_permission_check, context_event_manager_check, general_event_manager_check, context_organization_belong_check

from .models import e_Challenge, ChallengeState, e_ShortText_Question, e_Question
from .forms import ChallengeForm
from .filters import MyContextsChallengesFilter



class MyContextsChallengesFilterView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
    model = e_Challenge
    template_name = 'challenges/my_challenges_list.html'
    filterset_class = MyContextsChallengesFilter
    # pk_url_kwarg = 'contextCode'
    context_object_name = 'challenges'
    paginate_by = 9

    def get_queryset(self):

        # Show Challenges from this user's Contexts
        # TODO: Also only show Challenges created by this user?
        user_contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_eventManager').values_list('context')
        challenge_list = e_Challenge.objects.filter(created_by=self.request.user, event__context__in=user_contexts)

        return challenge_list
    
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        
        user_contexts = user_contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_eventManager').values_list('context')
        context['challenge_list'] = e_Challenge.objects.filter(created_by=self.request.user, event__context__in=user_contexts)
        context['filter'] = MyContextsChallengesFilter(self.request.GET, queryset=context['challenge_list'])
        
        return context

    def test_func(self):
        # Only Event Manager gets access to this page
        return general_event_manager_check(self.request.user)



class ChallengeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = e_Challenge
    form_class = ChallengeForm
    template_name = 'challenges/challenge_form.html'
    context_object_name = 'challenge'
    pk_url_kwarg = 'event_id'

    def test_func(self):
        event = e_ContextEvent.objects.get(pk=self.kwargs['event_id'])
        # Only Event Manager or Platform Admin can do this
        return context_event_manager_check(self.request.user, event.context) or is_platform_admin(self.request.user)

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



class ChallengeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = e_Challenge
    template_name = 'challenges/challenge_detail.html'
    pk_url_kwarg = 'challenge_id'
    context_object_name = 'challenge'

    # We override this method because we want to control who gets to see this page
    # TODO: Don't I just have to use the UserPassesTestMixin ??? I'm also doing this somewhere else in the project -> See where and fix
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
    
    def test_func(self):
        challenge = self.get_object()
        # Either Challenge is Public
        # Or user is part of its Organization
        return challenge.is_public or context_organization_belong_check(self.request.user, challenge.event.context.organization)



class ChallengeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_Challenge
    template_name = 'challenges/challenge_form.html'
    form_class = ChallengeForm
    pk_url_kwarg = 'challenge_id'
    context_object_name = 'challenge'

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['context'] = get_object_or_404(e_Context, pk=self.kwargs['pk'])
    #     return context

    def get_success_url(self):
        return reverse('challenge-detail', args=(self.get_object().id, ))

    def test_func(self):
        # Only Event Manager or Platform Admin can do this
        # TODO: Only author (or Platform Admin) of this Challenge can do this?
        return context_event_manager_check(self.request.user, self.get_object().event.context) or is_platform_admin(self.request.user)



class ChallengeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = e_Challenge
    template_name = 'challenges/challenge_confirm_delete.html'
    context_object_name = 'challenge'
    pk_url_kwarg = 'challenge_id'
    success_url = reverse_lazy('my-contexts-challenges-list')

    def form_valid(self, form):
        messages.success(self.request, "The Challenge was deleted successfully.")
        return super(ChallengeDeleteView,self).form_valid(form)
    
    def test_func(self):
        # Only Event Manager or Platform Admin can do this
        # TODO: Only author (or Platform Admin) of this Challenge can do this?
        return context_event_manager_check(self.request.user, self.get_object().event.context) or is_platform_admin(self.request.user)



class ChallengeManageView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = e_Challenge
    template_name = 'challenges/challenge_manage.html'
    pk_url_kwarg = 'challenge_id'
    context_object_name = 'challenge'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        challenge_id = self.kwargs['challenge_id']

        context['questions'] = e_Question.objects.filter(challenge=challenge_id)

        return context

    def test_func(self):
        challenge = self.get_object()
        # Only Event Manager or Platform Admin can do this
        return context_event_manager_check(self.request.user, self.get_object().event.context) or is_platform_admin(self.request.user)