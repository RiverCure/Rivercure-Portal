from django import forms

from users.models import User
from sensors.models import Sensor
from context.models import e_Context
from context.filters import ContextFilter
from notifications.models import Notification
from contributions.models import ContributionStatus
from rivercureportal.authorization import is_platform_admin, is_platform_admin_or_manager

from context.views.mesh import check_celery

from leaflet.forms.widgets import LeafletWidget

from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404

from django.db.models import Count, Q
from django.core.mail import send_mail
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView

from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import e_HydroFeature
from .forms import ContactForm
from .filters import UserFilter, HydroFeatureFilter, HydrofeatureContextsFilter
from .tasks import send_contact_email



class ProfileDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    context_object_name = 'u'
    template_name = 'rivercureportal/userprofile.html'

    def test_func(self):
        return is_platform_admin(self.request.user) or self.request.user == self.get_object()


@user_passes_test(is_platform_admin)
def users(request):
    if not is_platform_admin(request.user):
        return HttpResponse('Unauthorized', status=401)

    user_list = User.objects.all()
    user_filter = UserFilter(request.GET, queryset=user_list)

    context = {
        'users': user_list,
        'groups': Group.objects.all(),
        'filter':  user_filter,
    }

    return render(request, 'rivercureportal/users.html', context)


def home(request):

    # context = {
    #     'users': User.objects.all(),
    #     'groups': Group.objects.all(),
    #     'contexts': e_Context.objects.all(),
    #     'recent_context': e_Context.objects.all().first(),
    #     'recent_sensor': Sensor.objects.all().first()
    # }

    # return render(request, 'rivercureportal/home.html', context)
    return redirect('public-contexts')

def about(request):
    return render(request, 'rivercureportal/about.html')


class HydroFeatureListView(LoginRequiredMixin, ListView):
    model = e_HydroFeature
    context_object_name = 'hydrofeatures'
    template_name = 'rivercureportal/hydrofeature_list.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = e_HydroFeature.objects.all()
        filter = HydroFeatureFilter(self.request.GET, queryset.order_by('Name'))
        return filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        filter = HydroFeatureFilter(self.request.GET, queryset)
        context["filter"] = filter
        return context


class HydroFeatureForm(forms.ModelForm):
    class Meta:
        model = e_HydroFeature
        fields = ['Name', 'type', 'PartOf', 'flowsInto', 'geom']
        widgets = {'geom': LeafletWidget()}


class HydroFeatureCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = e_HydroFeature
    form_class = HydroFeatureForm
    template_name = 'rivercureportal/hydrofeature_form.html'
    success_url = reverse_lazy('hydrofeature-list')

    def test_func(self):
        return is_platform_admin_or_manager(self.request.user)


class HydroFeatureUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_HydroFeature
    context_object_name = 'hydrofeature'
    template_name = 'rivercureportal/hydrofeature_form.html'
    form_class = HydroFeatureForm
    success_url = reverse_lazy('hydrofeature-list')

    def test_func(self):
        return is_platform_admin_or_manager(self.request.user)


class HydroFeatureDetailView(DetailView):
    model = e_HydroFeature
    context_object_name = 'Hydrofeatures'
    template_name = 'rivercureportal/hydrofeature_detail.html'

    def get_context_data(self, **kwargs):
        hydrofeature = self.get_object()

        context = super().get_context_data(**kwargs)
        context['contexts'] = e_Context.objects.filter(hydroFeature=hydrofeature)
        
        return context

class HydroFeatureContextsListView(ListView):
    model = e_Context
    template_name = 'rivercureportal/hydrofeature_context_list.html'
    filterset_class = HydrofeatureContextsFilter
    context_object_name = 'hydrofeature_contexts'
    pk_url_kwarg = 'hydrofeaturePk'
    paginate_by = 9

    def get_queryset(self):
        hydrofeature_pk = self.kwargs['pk']
        hydrofeature = get_object_or_404(e_HydroFeature, pk=hydrofeature_pk)

        # Order by number of Accepted contributions belonging to this Context (from higher to lower)
        # Ordering by code also because of repeating results (See https://stackoverflow.com/questions/5044464/django-pagination-is-repeating-results)
        acceptedContributions = Count("e_contextcontribution", filter=Q(e_contextcontribution__state=ContributionStatus.ACCEPTED))
        context_list = e_Context.objects.filter(isPublic=True, hydroFeature=hydrofeature).annotate(acceptedContributions=acceptedContributions).order_by('-acceptedContributions', 'code')
        return context_list
    

    # TODO: Filtering not working?
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        hydrofeature_pk = self.kwargs['pk']
        hydrofeature = get_object_or_404(e_HydroFeature, pk=hydrofeature_pk)

        # Order by number of Accepted contributions belonging to this Context (from higher to lower)
        # Ordering by code also because of repeating results (See https://stackoverflow.com/questions/5044464/django-pagination-is-repeating-results)
        acceptedContributions = Count("e_contextcontribution", filter=Q(e_contextcontribution__state=ContributionStatus.ACCEPTED))
        context['context_list'] = e_Context.objects.filter(isPublic=True, hydroFeature=hydrofeature).annotate(acceptedContributions=acceptedContributions).order_by('-acceptedContributions', 'code')
        context['filter'] = HydrofeatureContextsFilter(self.request.GET, queryset=context['context_list'])
        context['hydrofeature'] = hydrofeature

        return context


class HydroFeatureDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = e_HydroFeature
    context_object_name = 'Hydrofeatures'
    template_name = 'rivercureportal/hydrofeature_confirm_delete.html'
    success_url = reverse_lazy('hydrofeature-list')

    def test_func(self):
        return is_platform_admin_or_manager(self.request.user)


@login_required
def clearNotifications(request):
    notifications = Notification.objects.filter(recipient=request.user)
    if notifications.exists():
        notifications.mark_all_as_read()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    context_object_name = 'notifications'
    template_name = 'rivercureportal/notification_list.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        if 'HTTP_REFERER' in self.request.META:
            context["previous_page"] = self.request.META['HTTP_REFERER']
        else:
            context["previous_page"] = reverse('rivercure-home')
        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
    name = 'Edit user'
    model = User
    context_object_name = 'u'
    template_name = 'rivercureportal/user_form.html'
    fields = ['groups']

    def get_success_url(self):
        return reverse_lazy('profile-detail', args=(self.get_object().pk,))

    def test_func(self):
        return is_platform_admin(self)

class ContactView(LoginRequiredMixin, FormView):
    form_class = ContactForm
    template_name = "rivercureportal/contact.html"

    def get_success_url(self):
        return reverse("contact")

    def form_valid(self, form):
        # email = form.cleaned_data.get("email")
        email = self.request.user.email
        subject = form.cleaned_data.get("subject")
        message = form.cleaned_data.get("message")

        # Celery
        # contact = {
        #     'from_email': email,
        #     'subject': subject,
        #     'message': message
        # }

        # if check_celery():
        #     task = send_contact_email.delay(contact)
        #     messages.success(self.request, 'Thank you for your contact!')
        # else:  # Celery offline
        #     messages.error(self.request, 'Background process offline: Contact admin.')

        # Debug
        full_message = f"""
            Received message below from {email}
            Subject - {subject}
            ________________________


            {message}
            """
        send_mail(
            subject=subject,
            message=full_message,
            from_email=email,
            recipient_list=['to@email.com'],
        )
        return super(ContactView, self).form_valid(form)
