from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django_filters.views import FilterView
from django.db.models import Case, When, Value, Count

from ..models import e_Context, ContextMembership
from ..filters import ModeratorAddFilter, ModeratorFilter, ModeratorContextFilter, ModeratorContextContributionFilter
from .authorization import *
from .prepare_files import *
from organization.models import Membership
from organization.authorization import belongs_to_organization
from contributions.models import e_ContextContribution, ContributionStatus

class ModeratorListView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
    model = User
    template_name = 'context/moderator/moderator_list.html'
    context_object_name = 'users'
    ordering = ['first_name', 'last_name'] # TODO: Working?
    pk_url_kwarg = 'contextCode'
    filterset_class = ModeratorFilter
    paginate_by = 5

    def get_queryset(self):
        _context = e_Context.objects.get(pk=self.kwargs['contextCode'])
        members = ContextMembership.objects.filter(context=_context, permission='context_moderator')

        return members

    def get_context_data(self, **kwargs):
        context_code = self.kwargs['contextCode']
        _context = e_Context.objects.get(pk=context_code)

        context = super(ModeratorListView, self).get_context_data(**kwargs)
        context['context'] = _context
        context['canEdit'] = context_organization_edit_permission_check(self.request.user, _context.organization) # Only Org or Context Managers can edit Moderators of a Context
        members = ContextMembership.objects.filter(context=context_code, permission='context_moderator')
        context['filter'] = ModeratorFilter(self.request.GET, queryset=members)
        return context
    
    def test_func(self):
        _context = e_Context.objects.get(pk=self.kwargs['contextCode'])
        return belongs_to_organization(self.request.user, _context.organization)

class ModeratorAddListView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
    model = User
    template_name = 'context/moderator/moderator_add_list.html'
    context_object_name = 'users'
    ordering = ['first_name', 'last_name'] # TODO: Working?
    pk_url_kwarg = 'contextCode' # = self.kwargs['contextCode']
    filterset_class = ModeratorAddFilter
    paginate_by = 5

    def get_queryset(self):
        _context = e_Context.objects.get(pk=self.kwargs['contextCode']) # TODO: Change these _context to just self.kwargs['contextCode'] when possible
        # Only show organization members that are not already context moderator's for that context
        moderators = ContextMembership.objects.filter(context=_context, permission='context_moderator').values('user')
        members = Membership.objects.filter(organization=_context.organization, permission='org_member').exclude(user__in=moderators)

        return members

    def get_context_data(self, **kwargs):
        _context = e_Context.objects.get(pk=self.kwargs['contextCode'])

        context = super(ModeratorAddListView, self).get_context_data(**kwargs)
        context['context'] =  _context
        # Only show organization members that are not already context moderator's for that context
        moderators = ContextMembership.objects.filter(context=_context, permission='context_moderator').values('user')
        org_members = Membership.objects.filter(organization=_context.organization, permission='org_member').exclude(user__in=moderators)
        # Filter
        context['filter'] = ModeratorAddFilter(self.request.GET, queryset=org_members)

        return context

    def test_func(self):
        _context = e_Context.objects.get(pk=self.kwargs['contextCode'])
        return context_organization_edit_permission_check(self.request.user, _context.organization)

@login_required
def contextModeratorAdd(request, contextCode, userId):
    _context = get_object_or_404(e_Context, pk=contextCode)
    user = get_object_or_404(User, pk=userId)
    organization = _context.organization

    # Make sure only Organization Manager and Context Manager can do this
    # And that the user belongs to the Org
    if not context_organization_edit_permission_check(request.user, organization.id) or not context_organization_belong_check(user, organization): # TODO: Is this working? # TODO: Substitute context_organization_belong_check with belongs_to_organization from organization/authorization.py !!!
        return HttpResponseRedirect(reverse('moderator-list', args=[contextCode]))
    
    # Make sure user is not already a Moderator
    if context_moderator_check(user, _context):
        return HttpResponseRedirect(reverse('moderator-list', args=[contextCode]))
    
    if user and _context:
        member = ContextMembership(user=user, context=_context, permission='context_moderator')
        member.save()

        # TODO: Send notifs

    return redirect('moderator-list', contextCode)


@login_required
def contextModeratorRemove(request, contextCode, userId):
    _context = get_object_or_404(e_Context, pk=contextCode)

    # Make sure only Organization Manager and Context Manager can do this
    if not context_organization_edit_permission_check(request.user, _context.organization.id):
        return HttpResponseRedirect(reverse('moderator-list', args=[contextCode]))
    
    user = get_object_or_404(User, pk=userId)
    context_membership_user = get_object_or_404(ContextMembership, user=user, context=_context, permission='context_moderator')

    if context_membership_user:
        context_membership_user.delete()

        # TODO: Send notifs
    
    return redirect('moderator-list', contextCode)

# TODO: Mudar nomes em que está ListView (e na verdade é uma FilterView) para FilterView
class ModeratorContextsListView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
    model = e_Context
    template_name = 'context/moderator/moderator_my_context_list.html'
    context_object_name = 'contexts'
    filterset_class = ModeratorContextFilter
    paginate_by = 6

    def get_queryset(self):
        # Get Contexts for which this user is a Moderator
        # And order them by number of pending contributions (hight to low)
        pendingContributions = Count("context__e_contextcontribution", filter=Q(context__e_contextcontribution__state=ContributionStatus.PENDING))
        contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_moderator').annotate(pendingContributions=pendingContributions).order_by('-pendingContributions', 'context__code')
        # contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_moderator')
        return contexts

    def get_context_data(self, **kwargs):
        context = super(ModeratorContextsListView, self).get_context_data(**kwargs)
        # Filter
        pendingContributions = Count("context__e_contextcontribution", filter=Q(context__e_contextcontribution__state=ContributionStatus.PENDING))
        contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_moderator').annotate(pendingContributions=pendingContributions).order_by('-pendingContributions', 'context__code')
        # contexts = ContextMembership.objects.filter(user=self.request.user, permission='context_moderator')
        context['filter'] = ModeratorContextFilter(self.request.GET, queryset=contexts)

        return context

    def test_func(self):
        # User must be a Moderator (in some Context)
        return general_moderator_check(self.request.user)

# TODO: Should I change this to be in contributions app ?
class ModeratorContextContributionListView(LoginRequiredMixin, UserPassesTestMixin, FilterView):
    model = e_ContextContribution
    template_name = 'context/moderator/moderator_context_contribution_list.html'
    context_object_name = 'contributions'
    pk_url_kwarg = 'contextCode' # = self.kwargs['contextCode']
    filterset_class = ModeratorContextContributionFilter
    paginate_by = 10

    def get_queryset(self):
        # Get this Context's Contributions
        # PEDNING Contributions come first. Done as seen in: https://stackoverflow.com/questions/48569659/django-how-would-i-create-a-sort-for-a-query-to-put-one-specific-element-first
        # TODO: Perhaps redo with: https://www.pixiebrix.com/blog/sort-django-queryset-by-custom-order/
        contributions = e_ContextContribution.objects.filter(context=self.kwargs['contextCode']).annotate(cont_state=Case(
            When(state=ContributionStatus.PENDING, then=Value(True)))
        ).order_by('cont_state', 'creationDateTime') # TODO: Is this actually working?
        return contributions

    def get_context_data(self, **kwargs):
        context = super(ModeratorContextContributionListView, self).get_context_data(**kwargs)
        context['context'] = e_Context.objects.get(pk=self.kwargs['contextCode'])
        # Filter
        contributions = e_ContextContribution.objects.filter(context=self.kwargs['contextCode']).annotate(cont_state=Case(
            When(state=ContributionStatus.PENDING, then=Value(True)))
        ).order_by('cont_state', 'creationDateTime') # TODO: Is this actually working?
        context['filter'] = ModeratorContextContributionFilter(self.request.GET, queryset=contributions)

        return context

    def test_func(self):
        # User must be a Moderator of this Context
        return context_moderator_check(self.request.user, self.kwargs['contextCode'])
    