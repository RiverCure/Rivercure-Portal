from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
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
from django.http import HttpResponseRedirect
from rivercureportal.views import is_admin

def is_org_manager(obj):
    try:
        organization_id = obj.kwargs.get('pk')
        return Membership.objects.filter(organization_id=organization_id, user=obj.request.user, permission='org_manager').exists()
    except:
        return False

def is_org_manager_check(user, organization_id):
    try:
        return Membership.objects.filter(organization_id=organization_id, user=user, permission='org_manager').exists()
    except:
        return False

class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organization/organization_list.html'
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
    template_name = 'organization/organization_form.html'
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
    template_name = 'organization/organization_detail.html'

    def get_context_data(self, **kwargs):
        context = super(OrganizationDetailView, self).get_context_data(**kwargs) # get the default context data
        context['managers'] = Membership.objects.filter(organization=self.get_object(), permission='org_manager')
        context['isManager'] = is_org_manager(self)
        return context

class OrganizationUpdateView(UserPassesTestMixin, UpdateView):
    name = 'Edit organization'
    model = Organization
    context_object_name = 'organization'
    fields = ['name', 'type', 'country', 'city']

    def get_success_url(self):
        return reverse_lazy('organization-detail', args=(self.get_object().id,))

    def test_func(self):
        return is_org_manager(self) and self.get_object().is_active

class OrganizationManageView(UserPassesTestMixin, ListView):
    model = User
    template_name = 'organization/organization_manage.html'
    context_object_name = 'users'
    paginate_by = 10
    ordering = ['-id'] # newer first

    def setup(self, request, *args, **kwargs):
        notification_id = request.GET.get('notification')
        if request.GET.get('notification') is not None:
            # To read notifications, for both managers and non-managers
            notification = Notification.objects.filter(pk=notification_id)
            if notification.first():
                notification.mark_as_read()

        return super().setup(request, *args, **kwargs)

    def test_func(self):
        return is_org_manager(self)

    def get_context_data(self, **kwargs):
        context = super(OrganizationManageView, self).get_context_data(**kwargs) # get the default context data
        
        organization_id = self.kwargs.get('pk')
        organization = Organization.objects.get(pk=organization_id)
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
    context_object_name = 'organization'
    template_name = 'organization/organization_role_form.html'
    fields = ['permission']

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
        cond2 = Membership.objects.filter(organization=organization, permission='org_manager').count() == 1 and self.get_object().permission == 'org_manager' and is_admin(self.request.user)
        return (cond1 or cond2) and organization.is_active

class OrganizationManageManagersView(UserPassesTestMixin, ListView):
    model = User
    template_name = 'organization/organization_manage_managers.html'
    context_object_name = 'users'
    paginate_by = 10
    ordering = ['-id'] # newer first

    def test_func(self):
        return is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(OrganizationManageManagersView, self).get_context_data(**kwargs) # get the default context data
        
        organization_id = self.kwargs.get('pk')
        organization = Organization.objects.get(pk=organization_id)
        context['organization'] = organization
        context['managers'] = Membership.objects.filter(organization=organization, permission='org_manager')

        return context

@login_required
def organizationAccessRequest(request, pk):

    organization = get_object_or_404(Organization, pk=pk)
    user = request.user
    
    if (not Membership.objects.filter(user=user, organization=organization).exists()) and organization.is_active == True:
        accessRequest = Membership(organization=organization, user=user)
        accessRequest.save()

        managers = User.objects.filter(membership__in=Membership.objects.filter(organization_id=pk, permission='org_manager'))
        notify.send(sender=user, recipient=managers, action_object=organization, verb=f"{user.username} requested to enter the organization {organization.name}")

    return redirect('organization-list')

@login_required
def organizationAccessRequestCancel(request, pk):

    organization = get_object_or_404(Organization, pk=pk)
    user = request.user
    # Make sure an user doesn't request to two organizations at the same time
    membership_user = Membership.objects.filter(user=user, organization=organization).first()
    if membership_user and organization.is_active == True:
        membership_user.delete()

    notifications = Notification.objects.filter(verb=f"{user.username} requested to enter the organization {organization.name}")
    if notifications is not None:
        notifications.mark_as_read()

    return redirect('organization-list') 


@login_required
def organizationAccessRequestDeny(request, pk1, pk2):
    if not is_org_manager_check(request.user, pk1):
        return HttpResponseRedirect(reverse('rivercure-home'))

    organization = get_object_or_404(Organization, pk=pk1)
    user = get_object_or_404(User, pk=pk2) # requester
    membership_user = get_object_or_404(Membership, user=user, organization=organization)

    if membership_user and organization.is_active == True:
        membership_user.delete()
    
        # Notify the user
        notify.send(sender=organization, recipient=user, action_object=organization, verb=f"You have been denied access to organization {organization.name}")
        # Notify all managers of the organization
        managers = User.objects.filter(membership__in=Membership.objects.filter(organization=organization, permission='org_manager')).exclude(pk=request.user.id)
        notify.send(sender=organization, recipient=managers, action_object=organization, verb=f"User {user} has been denied access to organization {organization.name}")

    return redirect('organization-manage', pk1)

@login_required
def organizationAccessRemove(request, pk1, pk2):
    if not is_org_manager_check(request.user, pk1) and not is_admin(request.user):
        return HttpResponseRedirect(reverse('rivercure-home'))

    organization = get_object_or_404(Organization, pk=pk1)
    user = get_object_or_404(User, pk=pk2)
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

    return redirect('organization-manage', pk1)

@login_required
def organizationAccessAllow(request, pk1, pk2):
    if not is_org_manager_check(request.user, pk1):
        return HttpResponseRedirect(reverse('rivercure-home'))

    organization = get_object_or_404(Organization, pk=pk1)
    user = get_object_or_404(User, pk=pk2)
    
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

    return redirect('organization-manage', pk1)

@login_required
def organizationReactivate(request, organization_id):
    if not is_admin(request.user):
        return HttpResponseRedirect(reverse('rivercure-home'))

    organization = get_object_or_404(Organization, pk=organization_id)
    organization.is_active = True
    organization.save()

    # Notify all members of the organization
    members = User.objects.filter(membership__in=Membership.objects.filter(organization=organization, access_granted=True)).exclude(pk=request.user.id)
    notify.send(sender=organization, recipient=members, action_object=organization, verb=f"Your organization {organization.name} has been reactivated by {request.user}")

    return redirect('organization-list')

@login_required
def organizationSuspend(request, organization_id):
    if not is_admin(request.user):
        return HttpResponseRedirect(reverse('rivercure-home'))

    organization = get_object_or_404(Organization, pk=organization_id)
    organization.is_active = False
    organization.save()

    # Notify all members of the organization
    members = User.objects.filter(membership__in=Membership.objects.filter(organization=organization, access_granted=True)).exclude(pk=request.user.id)
    notify.send(sender=organization, recipient=members, action_object=organization, verb=f"Your organization {organization.name} has been suspended by {request.user}")

    return redirect('organization-list')