from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django_filters.views import FilterView
from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.core import serializers
from common.utils import is_mobile


from django.core.files import File
from django.views.generic import ListView, CreateView, DetailView, DeleteView

from django.db.models.base import Model as Model
from django.contrib.gis.geos import Point
from django.db.models.query import QuerySet
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from rivercureportal.authorization import is_platform_admin

import datetime
from PIL import Image
from pyffmpeg import FFmpeg

from .models import e_ContextContribution, e_ContributionAttachment, ContributionStatus, e_ContributionReport, e_ContributionValidation, SituationChoices
from .forms import ContributionInitialForm, RejectionForm, ReportForm
from .filters import ContributionFilter, MyContributionsFilter
from .authorization import *
from .tasks import lat_long_to_address
from context.models import e_Context
from context.views.authorization import context_organization_edit_permission_check, context_moderator_check
from rivercureproject import settings
from context.views.mesh import check_celery


# class AllContributionsListView(LoginRequiredMixin, ListView):
#     model = e_ContextContribution
#     template_name = 'contributions/contribution_list.html'



class ContributionCreateView(LoginRequiredMixin, CreateView):
    model = e_ContextContribution
    form_class = ContributionInitialForm
    template_name = 'contributions/contribution_form.html'
    context_object_name = 'contribution'
    pk_url_kwarg = 'contextCode'

    def get_success_url(self):
        return reverse('contribution-detail', args=(self.object.id, ))

    def get_context_data(self, **kwargs):
        context_code = self.kwargs['contextCode']

        context = super().get_context_data(**kwargs)
        context['context'] = get_object_or_404(e_Context, code=context_code)
        context['context_code'] = self.kwargs['contextCode']
        # Serialize Context into JSON
        context['context_json'] = serializers.serialize('json', [context['context']], fields=('code', 'geomExternalBoundary'))
        
        return context

    # def post(self, request, *args, **kwargs):
    #     form_class = self.get_form_class()
    #     form = self.get_form(form_class)
    #     if form.is_valid():
    #         return self.form_valid(form)
    #     else:
    #         return self.form_invalid(form)
    def form_invalid(self, form):
        messages.error(self.request, 'There is an error in the submission form. Please check what field(s) need to be adjusted.')
        return super().form_invalid(form)

    def form_valid(self, form):
        # Set metadata
        new_contribution = form.save(commit=False)

        lat = form.cleaned_data["lat"]
        long = form.cleaned_data["lng"]

        new_contribution.createdBy = self.request.user
        context_code = self.kwargs['contextCode']
        _context = e_Context.objects.get(code=context_code)
        new_contribution.context = _context
        new_contribution.creationDateTime = datetime.datetime.now()
        new_contribution.observationPlace = Point(long, lat)

        # Set extra data
        if (new_contribution.situationObserved == SituationChoices.FLOOD):
            new_contribution.floating_objects_time = form.cleaned_data['floating_objects_time']
            new_contribution.water_height = form.cleaned_data['water_height']
        elif (new_contribution.situationObserved == SituationChoices.TORNADO):
            new_contribution.velocity = form.cleaned_data['velocity']
            new_contribution.tornado_type = form.cleaned_data['tornado_type']

        # Save
        new_contribution.save()

        # Deal with files
        files = form.cleaned_data["file_field"]
        is_first_file = True
        for f in files:
            new_attachment = handle_uploaded_file(new_contribution, f)
            
            # If it's the first file in files, also save as thumbnail of Contribution
            if is_first_file:
                is_first_file = False
                

                # If is image, simply save
                if new_attachment.is_video_or_image() == 'image':
                    # new_contribution.thumbnail = f
                    new_contribution.thumbnail = new_attachment.file

                # If is video, first get thumbnail and then save
                else:
                    try:
                        ff = FFmpeg()

                        # oh god
                        input_path = new_attachment.file.path
                        input_path_no_extension = input_path.split('.')[0] 
                        output_path = input_path_no_extension + ".jpg"
                        ff.options("-i {} -ss 00:00:01.000 -vframes 1 {}".format(input_path, output_path))
                        thumb = open(output_path, "rb")
                        thumb_django_file = File(thumb) # As seen in: https://www.revsys.com/tidbits/loading-django-files-from-code/
                        new_contribution.thumbnail = thumb_django_file
                    except:
                        # TODO: do a clean_files method or something where we check the length of the video and only allow form to be valid if its > 1 second
                        raise Exception("Video needs to be longer than 1 second in order to have a thumbnail.")

                new_contribution.save()
        
        # If there are no files, add default thumbnail depending on situationObserved
        if len(files) == 0:
            situation = str(new_contribution.situationObserved).lower()
            # default_img_path = "{}contributions/situation_icons/{}.png".format(settings.MEDIA_URL, situation)
            default_img_path = "media/contributions/situation_icons/{}.png".format(situation)
            thumb = open(default_img_path, "rb")
            thumb_django_file = File(thumb)
            new_contribution.thumbnail = thumb_django_file
            new_contribution.save()

        
        # Create and save e_ContributionValidation object
        validation = e_ContributionValidation(contribution=new_contribution, state=ContributionStatus.PENDING, validated_by=self.request.user)
        validation.save()
        
        # Send success message (to be shown in detail page)
        messages.success(self.request, 'Thank you for submitting your Contribution! Your participation is very valuable to the RiverCure Portal.')

        # TODO: Send confirmation email to user

        return super().form_valid(form)



class ContributionListView(FilterView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_list.html'
    filterset_class = ContributionFilter
    pk_url_kwarg = 'contextCode'
    context_object_name = 'contributions'
    paginate_by = 9

    def get_queryset(self):

        context_code = self.kwargs['contextCode']
        contribution_list = e_ContextContribution.objects.filter(context=context_code, state=ContributionStatus.ACCEPTED).order_by('-creationDateTime') # Only show Accepted Contributions

        return contribution_list
    
    def get_context_data(self, **kwargs):
        context_code = self.kwargs['contextCode']

        context = super().get_context_data(**kwargs)
        context['MEDIA_URL'] = settings.MEDIA_URL
        context['context'] = get_object_or_404(e_Context, code=context_code)
        context['contribution_list'] = e_ContextContribution.objects.filter(context=context_code, state=ContributionStatus.ACCEPTED).order_by('-creationDateTime') # Only show Accepted Contributions
        context['filter'] = ContributionFilter(self.request.GET, queryset=context['contribution_list'])
        context['is_mobile'] = is_mobile(self.request)
        
        return context



class ContributionDetailView(DetailView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_detail.html'
    pk_url_kwarg = 'contributionId'
    context_object_name = 'contribution'

    # We override this method because we want to control who gets to see this page
    # As seen in: https://stackoverflow.com/a/42653231/12387341
    def get_object(self, queryset=None):
        contribution = super().get_object(queryset)

        # If Contribution is PENDING or REJECTED
        if contribution.state != ContributionStatus.ACCEPTED:
            # And if user is not author OR moderator OR context manager OR org manager (of the contribution's context and organization)
            # TODO: OR IS ADMIN!!
            if not (author_of_contribution_check(self.request.user, contribution) or context_moderator_check(self.request.user, contribution.context) or context_organization_edit_permission_check(self.request.user, contribution.context.organization)):
                # Then the user should not get access to the page
                # TODO: use redirect instead. See how I did in challenges
                # TODO: uniformize all views
                raise Http404()
        
        # Otherwise (Contribution is ACCEPTED or user has correct permissions) then just show it
        return contribution
                

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        org = self.get_object().context.organization

        context['contribution_media_list'] = e_ContributionAttachment.objects.filter(contribution=self.get_object().pk)
        context['MEDIA_URL'] = settings.MEDIA_URL
        context['isContextOrOrgManager'] = context_organization_edit_permission_check(user, org)
        context['isMod'] = context_moderator_check(self.request.user, self.get_object().context.code)
        context['form'] = RejectionForm()
        context['report_form'] = ReportForm()
        context['reports'] = e_ContributionReport.objects.filter(contribution=self.get_object().pk).order_by('-report_datetime')
        context['validations'] = e_ContributionValidation.objects.filter(contribution=self.get_object().pk).order_by('-validation_datetime')
        context['nextContribution'] = e_ContextContribution.objects.filter(context=self.get_object().context.code, state=ContributionStatus.PENDING).order_by('creationDateTime').first()
        context['is_mobile'] = is_mobile(self.request)
        return context
    

class MyContributionsListView(LoginRequiredMixin, FilterView):
    model = e_ContextContribution
    template_name = 'contributions/my_contributions_list.html'
    context_object_name = 'contributions'
    filterset_class = MyContributionsFilter
    paginate_by = 9

    def get_queryset(self):

        user = self.request.user

        contribution_list = e_ContextContribution.objects.filter(createdBy=user).order_by('-creationDateTime')

        return contribution_list
    
    def get_context_data(self, **kwargs):
        user = self.request.user

        context = super().get_context_data(**kwargs)
        context['MEDIA_URL'] = settings.MEDIA_URL
        context['contribution_list'] = e_ContextContribution.objects.filter(createdBy=user).order_by('-creationDateTime')
        context['filter'] = MyContributionsFilter(self.request.GET, queryset=context['contribution_list'])
        
        return context



class ContributionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = e_ContextContribution
    template_name = 'contributions/contribution_confirm_delete.html'
    pk_url_kwarg = 'contributionId'
    success_url = reverse_lazy('my-contributions')
    context_object_name = 'contribution'

    def test_func(self):
        # Author, Event Manager or Platform Admin can delete the Contribution
        return author_of_contribution_check(self.request.user, self.get_object()) or context_moderator_check(self.request.user, self.get_object().context) or is_platform_admin(self.request.user)


@login_required
def contributionAccept(request, contributionId):
    contribution = get_object_or_404(e_ContextContribution, pk=contributionId)

    # Make sure only (Context) Moderator can do this
    if not context_moderator_check(request.user, contribution.context):
        return HttpResponseRedirect(reverse('contribution-detail', args=[contributionId]))
    
    # Change Contribution state to ACCEPTED if we are allowed to
    if contribution and contribution.can_accept():

        accept_contribution(contribution, request.user, request)
    
        # TODO: Send notifs

    return redirect('contribution-detail', contributionId)

def accept_contribution(contribution, user, request):
    """
    Helper function that accepts a Contribution.
    (1) If Contribution was REPORTED, clears all reports (ONLY do this for accept, not reject)
    (2) Saves the details of latest validation in the Contribution object
    (3) Creates an e_ContributionValidation object

    contribution: Contribution object
    user: User object
    """
    # If Contribution was REPORTED
    if contribution.state == ContributionStatus.REPORTED:
        # Clear all reports made to this Contribution # TODO: One day, stop doing this and just keep every report ever made
        deleted_reports = e_ContributionReport.objects.filter(contribution=contribution).delete()

    # Put details of latest validation in Contribution
    contribution.accept()
    contribution.last_validated_by = user
    contribution.last_validation_datetime = datetime.datetime.now()


    # Create a e_ContributionValidation object
    validation = e_ContributionValidation(contribution=contribution, state=ContributionStatus.ACCEPTED, validated_by=user)

    # Save everything
    contribution.save()
    validation.save()

    # If Contribution has an empty address
    if contribution.observationAddress == '':
        # Reverse geocode to get address -> Send this task to Celery
        if check_celery():
            task = lat_long_to_address.delay(contribution.pk)
        else:  # Celery offline
            messages.error(request, 'Background process offline: Contact admin.')

@login_required
def contributionReject(request, contributionId):
    contribution = get_object_or_404(e_ContextContribution, pk=contributionId)

    # Make sure only (Context) Moderator can do this
    if not context_moderator_check(request.user, contribution.context):
        return HttpResponseRedirect(reverse('contribution-detail', args=[contributionId]))
    
    # create a form instance and populate it with data from the request:
    form = RejectionForm(request.POST)

    if form.is_valid() and contribution and contribution.can_reject():

        reject_contribution(contribution, request.user, form.cleaned_data['last_rejection_reason'])
        
        # TODO: Send notifs
        
        return HttpResponseRedirect(reverse('contribution-detail', args=[contributionId]))
    
    return redirect('contribution-detail', contributionId)


def reject_contribution(contribution, user, rejection_reason):
    """
    Helper function that rejects a Contribution.
    (1) Saves details of latest validation in the Contribution object
    (2) Creates an e_ContributionValidation object

    contribution: Contribution object
    user: User object
    rejection_reason: Reason why this Contribution is being rejected. Can be obtained through a form.
    """
    # Save details of latest validation in Contribution
    contribution.reject()
    contribution.last_rejection_reason = rejection_reason
    contribution.last_validated_by = user
    contribution.last_validation_datetime = datetime.datetime.now()

    # Create a e_ContributionValidation object
    validation = e_ContributionValidation(contribution=contribution, state=ContributionStatus.REJECTED, validated_by=user, rejection_reason=rejection_reason)

    # Save everything
    contribution.save()
    validation.save()


@login_required
def contributionReport(request, contributionId):
    contribution = get_object_or_404(e_ContextContribution, pk=contributionId)

    # Any logged-in user can do this
    # Create a form instance and populate it with data from the request:
    form = ReportForm(request.POST)

    if form.is_valid() and contribution and (contribution.state == ContributionStatus.ACCEPTED):

        # Create e_ReportReason object
        report = e_ContributionReport(contribution=contribution, reported_by=request.user, reason=form.cleaned_data['reason'])

        # If the condition/threshold is met, actually change the state of the Contribution to REPORTED.
        # Otherwise we're only saving a record of a Report
        if report_contribution_condition(contribution):
            # Report Contribution
            contribution.report()

            # Create e_ContributionValidation with state REPORTED and no validated_by user
            validation = e_ContributionValidation(contribution=contribution, state=ContributionStatus.REPORTED, validated_by=None)

            # Save
            contribution.save()
            validation.save()

        # Save
        report.save()
        
        # TODO: Send notifs
        
        return HttpResponseRedirect(reverse('contribution-list', args=[contribution.context.code]))
    
    return redirect('contribution-list', args=[contribution.context.code])

# TODO: CHANGE THIS TO A BETTER CONDITION!!!
def report_contribution_condition(contribution):
    """
    Check whether this Contribution can change to state REPORTED
    """
    all_reports = e_ContributionReport.objects.filter(contribution=contribution)

    # TODO: CHANGE THIS TO A BETTER CONDITION!!!
    if not all_reports:
        return True
    return all_reports.count() > 0

# Helper functions
def handle_uploaded_file(contribution, uploaded_file):
    """
    Helper function that saves attachment and updates total_file_size of Contribution

    (1) Creates and saves e_ContributionAttachment object
    
    (2) Saves this file's size in its e_ContributionAttachment object
    
    (3) Adds to and saves the total size of the Contribution
    """
    # Create e_ContributionAttachment object
    attachment = e_ContributionAttachment.objects.create(file=uploaded_file, contribution=contribution)
    # Save
    attachment.save()

    # Save file size
    # Only do this after creating and saving the e_ContributionAttachment object for the first time because of the resizing we do on save
    # Only after doing that resizing do we get and save the image's size
    file_size = bytes_to_megabytes(attachment.file.size)
    attachment.file_size = file_size
    # Add to total size of Contribution
    contribution.total_file_size = contribution.total_file_size + file_size
    # Save everything
    attachment.save()
    contribution.save()

    return attachment



def bytes_to_megabytes(bytes):
    """
    Convert Bytes to Megabytes

    bytes: int to be converted
    """
    kbytes = bytes / 1024
    mbytes = kbytes / 1024
    converted_value = round(mbytes, 3)
    return converted_value



def make_thumbnail(contribution, attachment):

    file_path = attachment.file.path

    ## Image
    if attachment.is_video_or_image() == 'image':
        
        # Make even smaller
        output_size = (150, 150)
        
        original_img = Image.open(file_path)
        thumb = original_img.copy()

        if thumb.height > 150 or thumb.width > 150:
            thumb.thumbnail(output_size)
            contribution.thumbnail = thumb
            contribution.save()