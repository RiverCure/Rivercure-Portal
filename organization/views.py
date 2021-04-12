from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from .models import Organization, OrganizationAccessRequest
from django.urls import reverse_lazy
from users.models import Profile
from django.contrib.auth.decorators import login_required
from django.db import connection


class OrganizationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Organization
    fields = ['name', 'manager']
    # fields = ['name', 'type', 'country', 'city', 'manager']
    success_url = reverse_lazy('organization-list')

    def form_valid(self, form):
        organization = form.save(commit=True)
        organization.save()

        # Associate organization to manager
        user = Profile.objects.get(user__username=form.cleaned_data['manager'])
        user.organization = organization
        user.save()

        return super().form_valid(form)

    def test_func(self):
        if self.request.user.is_staff:
            return True
        else:
            return False


class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organization/organization_list.html'
    context_object_name = 'organizations'
    paginate_by = 10
    ordering = ['-id'] # newer first


    def get_context_data(self, **kwargs):
        context = super(OrganizationListView, self).get_context_data(**kwargs) # get the default context data
        context['user_organization'] = Profile.objects.get(pk=self.request.user.id).organization
        try:
            context['access_request'] = OrganizationAccessRequest.objects.get(requester=self.request.user)
        except:
            context['access_request'] = None
        # print(context['access_request'].organization)
        return context


class OrganizationDetailView(LoginRequiredMixin, DetailView):
    model = Organization
    context_object_name = 'organization'
    template_name = 'organization/organization_detail.html'

    # Creates a variable for the template to filter who can see the Add/delete buttons
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hasPerm'] = (self.get_object() in Organization.objects.filter(manager=self.request.user.id)) or self.request.user.is_staff
        return context

class OrganizationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Organization
    fields = ['name', 'type', 'country', 'city', 'isPublic']
    success_url = reverse_lazy('organization-list')
    
    def test_func(self):
        if (self.get_object() in Organization.objects.filter(manager=self.request.user.id)) or self.request.user.is_staff:
            return True
        else:
            return False

class OrganizationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView ):
    model = Organization
    context_object_name = 'organization'
    template_name = 'organization/organization_confirm_delete.html'
    success_url = reverse_lazy('organization-list')

    def test_func(self):
        if Organization.objects.filter(manager=self.request.user.id).exists() or self.request.user.is_staff:
            return True
        else:
            return False

class OrganizationManageView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = 'organization/organization_manage.html'
    context_object_name = 'userProfiles'
    paginate_by = 10
    ordering = ['-id'] # newer first

    def get_context_data(self, **kwargs):
        context = super(OrganizationManageView, self).get_context_data(**kwargs) # get the default context data
        
        organization_id = self.kwargs.get('pk')
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT au.id, username, email, TRUE as access_granted, org.manager_id
                FROM users_profile as up, auth_user as au, organization_organization as org
                WHERE organization_id = %s AND up.id = au.id AND org.id = %s
                UNION
                SELECT au.id, username, email, access_granted, org.manager_id
                FROM organization_organizationaccessrequest as oar, auth_user as au, organization_organization as org
                WHERE organization_id = %s AND oar.requester_id = au.id AND oar.access_granted = False AND org.id = %s;
                ''', 
                [organization_id, organization_id, organization_id, organization_id])
            
            results = self.dictfetchall(cursor)

        # print(row)
        print(results)
        context['users'] = results
        context['organization'] = Organization.objects.get(pk=organization_id)
        return context

    def dictfetchall(self, cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


#TODO: FOR ALL BELOW FUNCTIONS: USER VERFICATION (IF HAS PERMISSION)
@login_required
def organizationAccessRequest(request, pk):
    organization = pk
    user = request.user
    # Make sure an user doesn't request to two organizations at the same time
    if not OrganizationAccessRequest.objects.filter(requester=user).exists():
        accessRequest = OrganizationAccessRequest(organization_id=organization, requester=user)
        accessRequest.save()

    return redirect('organization-list')

@login_required
def organizationAccessRequestCancel(request, pk):
    organization = pk
    user = request.user
    # Make sure an user doesn't request to two organizations at the same time
    if OrganizationAccessRequest.objects.filter(requester=user).exists():
        OrganizationAccessRequest.objects.filter(requester=user).delete()

    return redirect('organization-list') 


@login_required
def organizationAccessRequestDeny(request, pk1, pk2):
    organization = pk1
    user = pk2

    if OrganizationAccessRequest.objects.filter(requester=user).exists():
        OrganizationAccessRequest.objects.filter(requester=user).delete()

    return redirect('organization-manage', organization)

@login_required
def organizationAccessRemove(request, pk1, pk2):
    organization = pk1
    user = pk2
    # Make sure an user doesn't request to two organizations at the same time
    if OrganizationAccessRequest.objects.filter(requester=user).exists():
        OrganizationAccessRequest.objects.filter(requester=user).delete()
    
    # Remove user from organization 
    userObj = Profile.objects.get(pk=user)
    userObj.organization = None
    userObj.save()

    return redirect('organization-manage', organization)

@login_required
def organizationAccessAllow(request, pk1, pk2):
    organization = pk1
    user = pk2
    # Make sure an user doesn't request to two organizations at the same time
    if OrganizationAccessRequest.objects.filter(requester=user).exists():
        OrganizationAccessRequest.objects.filter(requester=user).delete()
    
    # Add user to organizatiton
    # Remove user from organization 
    userObj = Profile.objects.get(pk=user)
    userObj.organization = Organization.objects.get(pk=organization)
    userObj.save()

    return redirect('organization-manage', organization) 