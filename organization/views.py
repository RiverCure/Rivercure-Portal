from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from .models import Organization
from .models import Organization, Membership
from django.urls import reverse, reverse_lazy
from users.models import Profile
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import connection
from notifications.signals import notify
from django.contrib.auth.models import User
from notifications.models import Notification
from django.contrib.auth.views import redirect_to_login
from .forms import CreateOrganizationForm
from datetime import datetime
from django.http import HttpResponseRedirect, HttpResponse
from rivercureportal.authorization import is_platform_admin
from organization.authorization import *
from django.contrib.auth.signals import user_logged_in
from django.contrib import messages

# Adds the default organization to the session, so that it is available in every view
def user_log_in_handler(sender, user, request, **kwargs):
    organization = Profile.objects.get(user=user).defaultOrganization
    request.session['organizationName'] = organization.name if organization else None

user_logged_in.connect(user_log_in_handler)

class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organization/list.html'
    context_object_name = 'organizations'
    paginate_by = 10
    ordering = ['-id'] # newer first

    def get_context_data(self, **kwargs):
        context = super(OrganizationListView, self).get_context_data(**kwargs) # get the default context data

        organizations_accepted = Organization.objects.filter(members=self.request.user, membership__access_granted=True)
        organizations_pending  = Organization.objects.filter(members=self.request.user, membership__access_granted=False)
        for elem in context['organizations']:
            if elem in organizations_accepted:
                elem.permission = Membership.objects.get(user=self.request.user, organization=elem).permission
            elif elem in organizations_pending:
                elem.pending = True

        return context

class OrganizationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    name = 'New organization'
    model = Organization
    template_name = 'organization/form.html'
    form_class = CreateOrganizationForm
    success_url = reverse_lazy('organization-list')

    def form_valid(self, form):
        currentTime = datetime.now()
        organization = form.save(commit=False)
        # Add metadata to organization
        organization.created_by = self.request.user
        organization.create_date = currentTime
        organization.save()

        # Set manager permissions
        manager = form.cleaned_data['manager']
        # Create membership entry for manager
        membership = Membership(user=manager, organization=organization, access_granted=True, access_grant_date=currentTime, permission='org_manager')
        membership.save()

        # Notify new manager
        notify.send(sender=organization, recipient=manager, action_object=organization, verb=f"You have been assigned management of the new organization {organization.name} by {self.request.user}")

        return super().form_valid(form)

    def test_func(self):
        return self.request.user.groups.filter(name='Admin').exists()


class OrganizationDetailView(LoginRequiredMixin, DetailView):
    model = Organization
    context_object_name = 'organization'
    template_name = 'organization/detail.html'
    pk_url_kwarg = 'organizationId'

    def get_context_data(self, **kwargs):
        user = self.request.user
        organization = self.get_object()

        context = super(OrganizationDetailView, self).get_context_data(**kwargs) # get the default context data
        context['managers'] = Membership.objects.filter(organization=organization, permission='org_manager')
        context['belongsToOrganization'] = belongs_to_organization(user, organization)
        context['isManager'] = is_org_manager(user, organization)
        context['isSensorManager'] = is_sensor_manager(user, organization)
        return context

class OrganizationUpdateView(UserPassesTestMixin, UpdateView):
    name = 'Edit organization'
    model = Organization
    context_object_name = 'organization'
    template_name = 'organization/form.html'
    fields = ['name', 'type', 'country', 'city']
    pk_url_kwarg = 'organizationId'

    def get_success_url(self):
        return reverse_lazy('organization-detail', args=(self.get_object().id,))

    def test_func(self):
        return is_org_manager(self.request.user, self.get_object()) and self.get_object().is_active

class OrganizationManageView(UserPassesTestMixin, ListView):
    model = User
    template_name = 'organization/manage.html'
    context_object_name = 'users'
    paginate_by = 10
    ordering = ['-id'] # newer first

    def setup(self, request, *args, **kwargs):
        notification_id = request.GET.get('notification')
        if notification_id is not None:
            # To read notifications, for both managers and non-managers
            notification = Notification.objects.filter(pk=notification_id)
            if notification.first():
                print(notification)
                notification.first().mark_as_read()

        return super().setup(request, *args, **kwargs)

    def test_func(self):
        return is_org_manager(self.request.user, self.kwargs.get('organizationId'))

    def get_context_data(self, **kwargs):
        organization_id = self.kwargs.get('organizationId')
        organization = get_object_or_404(Organization, pk=organization_id)

        context = super(OrganizationManageView, self).get_context_data(**kwargs) # get the default context data
        context['organization'] = organization
        context['members'] = Membership.objects.filter(organization=organization)

        return context

    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect('organization-list')
        else:
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())


class MemberRoleUpdateView(UserPassesTestMixin, UpdateView):
    name = 'Edit role'
    model = Membership
    context_object_name = 'membership'
    template_name = 'organization/role_form.html'
    fields = ['permission']
    pk_url_kwarg = 'membershipId'

    def get_success_url(self):
        user = self.get_object().user
        organization = self.get_object().organization
        
        newRole = Membership.objects.get(user=user, organization=organization).get_permission_display()
        
        # Notify other managers
        managers = User.objects.filter(membership__in=Membership.objects.filter(organization=organization, permission='org_manager')).exclude(pk=self.request.user.id)
        notify.send(sender=organization, recipient=managers, action_object=organization, verb=f"User {user} role on organization {organization.name} has been changed to {newRole} by {self.request.user}")
        # Notify user
        notify.send(sender=organization, recipient=user, action_object=organization, verb=f"Your role on organization {organization.name} has been changed to {newRole} by {self.request.user}")

        return reverse('organization-manage', args=(self.get_object().organization.id,))

    def test_func(self):
        organization = self.get_object().organization
        cond1 = self.request.user in User.objects.filter(membership__in=Membership.objects.filter(organization=organization, permission='org_manager'))
        cond2 = Membership.objects.filter(organization=organization, permission='org_manager').count() == 1 and self.get_object().permission == 'org_manager' and is_platform_admin(self.request.user)
        return (cond1 or cond2) and organization.is_active

class OrganizationManageManagersView(UserPassesTestMixin, ListView):
    model = User
    template_name = 'organization/manage_managers.html'
    context_object_name = 'users'
    paginate_by = 10
    ordering = ['-id'] # newer first

    def test_func(self):
        return is_platform_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(OrganizationManageManagersView, self).get_context_data(**kwargs) # get the default context data
        
        organization_id = self.kwargs.get('organizationId')
        organization = get_object_or_404(Organization, pk=organization_id)
        context['organization'] = organization
        context['managers'] = Membership.objects.filter(organization=organization, permission='org_manager')

        return context

@login_required
def organizationAccessRequest(request, organizationId):

    organization = get_object_or_404(Organization, pk=organizationId)
    user = request.user
    
    if (not Membership.objects.filter(user=user, organization=organization).exists()) and organization.is_active == True:
        accessRequest = Membership(organization=organization, user=user)
        accessRequest.save()

        managers = User.objects.filter(membership__in=Membership.objects.filter(organization_id=organizationId, permission='org_manager'))
        notify.send(sender=user, recipient=managers, action_object=organization, verb=f"{user.username} requested to enter the organization {organization.name}")

    return redirect('organization-list')

@login_required
def organizationAccessRequestCancel(request, organizationId):

    organization = get_object_or_404(Organization, pk=organizationId)
    user = request.user
    # Make sure an user doesn't request to two organizations at the same time
    membership_user = Membership.objects.filter(user=user, organization=organization).first()
    if membership_user and organization.is_active == True:
        membership_user.delete()

    notifications = Notification.objects.filter(verb=f"{user.username} requested to enter the organization {organization.name}")
    if notifications is not None:
        notifications.first().mark_as_read()

    return redirect('organization-list') 


@login_required
def organizationAccessRequestDeny(request, organizationId, userId):
    if not is_org_manager_check(request.user, organizationId):
        return HttpResponseRedirect(reverse('rivercure-home'))

    organization = get_object_or_404(Organization, pk=organizationId)
    user = get_object_or_404(User, pk=userId) # requester
    membership_user = get_object_or_404(Membership, user=user, organization=organization)

    if membership_user and organization.is_active == True:
        membership_user.delete()
    
        # Notify the user
        notify.send(sender=organization, recipient=user, action_object=organization, verb=f"You have been denied access to organization {organization.name}")
        # Notify all managers of the organization
        managers = User.objects.filter(membership__in=Membership.objects.filter(organization=organization, permission='org_manager')).exclude(pk=request.user.id)
        notify.send(sender=organization, recipient=managers, action_object=organization, verb=f"User {user} has been denied access to organization {organization.name}")

    return redirect('organization-manage', organizationId)

@login_required
def organizationAccessRemove(request, organizationId, userId):
    if not is_org_manager_check(request.user, organizationId) and not is_platform_admin(request.user):
        return HttpResponseRedirect(reverse('rivercure-home'))

    organization = get_object_or_404(Organization, pk=organizationId)
    user = get_object_or_404(User, pk=userId)
    # Make sure an user doesn't request to two organizations at the same time
    membership_user = get_object_or_404(Membership, user=user, organization=organization)

    # Don't allow the last manager to be removed
    if Membership.objects.filter(organization=organization, permission='org_manager').count() == 1 and membership_user.permission == 'org_manager':
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
    if membership_user and organization.is_active == True:
        membership_user.delete()

        notify.send(sender=organization, recipient=user, action_object=organization, verb=f"Your access to organization {organization.name} has been removed")
        # Notify all managers of the organization
        managers = User.objects.filter(membership__in=Membership.objects.filter(organization=organization, permission='org_manager')).exclude(pk=request.user.id)
        notify.send(sender=organization, recipient=managers, action_object=organization, verb=f"User {user} access to organization {organization.name} has been removed")

    return redirect('organization-manage', organizationId)

@login_required
def organizationAccessAllow(request, organizationId, userId):
    if not is_org_manager_check(request.user, organizationId):
        return HttpResponseRedirect(reverse('rivercure-home'))

    organization = get_object_or_404(Organization, pk=organizationId)
    user = get_object_or_404(User, pk=userId)
    
    membership_user = Membership.objects.filter(user=user, organization=organization).first()
    if membership_user and organization.is_active == True:
        print(membership_user.access_granted)
        membership_user.access_granted = True
        membership_user.access_grant_date = datetime.now()
        membership_user.permission = 'org_member'
        print(membership_user.access_granted)
        membership_user.save()

        # Notify the user
        notify.send(sender=organization, recipient=user, action_object=organization, verb=f"You have been granted access to organization {organization.name}")
        # Notify all managers of the organization
        managers = User.objects.filter(membership__in=Membership.objects.filter(organization=organization, permission='org_manager')).exclude(pk=request.user.id)
        notify.send(sender=organization, recipient=managers, action_object=organization, verb=f"User {user} has been granted access to organization {organization.name}")

    return redirect('organization-manage', organizationId)

@login_required
@user_passes_test(is_platform_admin)
def organizationReactivate(request, organizationId):
    organization = get_object_or_404(Organization, pk=organizationId)
    organization.is_active = True
    organization.save()

    # Notify all members of the organization
    members = User.objects.filter(membership__in=Membership.objects.filter(organization=organization, access_granted=True)).exclude(pk=request.user.id)
    notify.send(sender=organization, recipient=members, action_object=organization, verb=f"Your organization {organization.name} has been reactivated by {request.user}")

    return redirect('organization-list')

@login_required
@user_passes_test(is_platform_admin)
def organizationSuspend(request, organizationId):
    organization = get_object_or_404(Organization, pk=organizationId)
    organization.is_active = False
    organization.save()

    # Notify all members of the organization
    members = User.objects.filter(membership__in=Membership.objects.filter(organization=organization, access_granted=True)).exclude(pk=request.user.id)
    notify.send(sender=organization, recipient=members, action_object=organization, verb=f"Your organization {organization.name} has been suspended by {request.user}")

    return redirect('organization-list')

@login_required
def organizationSetCurrent(request, organizationId):
    organization = get_object_or_404(Organization, pk=organizationId)
    request.session['organizationName'] = organization.name

    messages.success(request, f'You made organization {organization.name} your current organization')
    return redirect('organization-detail', organization.pk)