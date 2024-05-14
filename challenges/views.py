from django.urls import reverse, reverse_lazy
from django.http import Http404, HttpResponse
from django.forms import modelformset_factory, Textarea
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, redirect
from django_filters.views import FilterView

from django.views.generic import ListView, CreateView, DetailView, DeleteView, UpdateView

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required

from context.models import e_ContextEvent
from context.models import ContextMembership
from organization.models import Membership
from rivercureportal.authorization import is_platform_admin

from context.views.authorization import context_organization_edit_permission_check, context_event_manager_check, general_event_manager_check, context_organization_belong_check

from .models import e_Challenge, ChallengeState, e_Question, e_ShortText_Question, Question_Type, e_MultipleChoiceOption_Question, e_TrueFalse_Question
from .forms import ChallengeForm, QuestionForm, QuestionUpdateForm, QuestionShortTextForm, QuestionMultipleChoiceFormSet, QuestionTrueFalseFormSet
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
        context['short_text_question_form'] = QuestionShortTextForm()

        return context

    def test_func(self):
        # Only Event Manager or Platform Admin can do this
        return context_event_manager_check(self.request.user, self.get_object().event.context) or is_platform_admin(self.request.user)


# Not being used
class QuestionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = e_Question
    form_class = QuestionForm
    template_name = 'challenges/question_form.html'
    context_object_name = 'question'
    pk_url_kwarg = 'challenge_id'

    def get_success_url(self):
        return reverse('challenge-manage', args=(self.kwargs['challenge_id'], ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['challenge'] = e_Challenge.objects.get(pk=self.kwargs['challenge_id'])
        
        return context

    def form_invalid(self, form):
        messages.error(self.request, 'There is an error in the submission form. Please check what field(s) need to be adjusted.')
        return super().form_invalid(form)
    
    def form_valid(self, form):
        challenge = e_Challenge.objects.get(pk=self.kwargs['challenge_id'])

        new_question = form.save(commit=False)

        # Set metadata
        new_question.challenge = challenge
        new_question.created_by = self.request.user

        # TODO: If Short Text, ...

        # Save
        new_question.save()

        # Send success message (to be shown in Challenge detail page)
        messages.success(self.request, 'Your Question has been created successfully.')

        return super().form_valid(form)
    
    def test_func(self):
        challenge = e_Challenge.objects.get(pk=self.kwargs['challenge_id'])
        # Only Event Manager or Platform Admin can do this
        return context_event_manager_check(self.request.user, challenge.event.context) or is_platform_admin(self.request.user)

@login_required
def question_create(request, challenge_id):

    # TODO: Only allow Context EM and Platform Admin to do this

    if request.method == 'POST':
        challenge = e_Challenge.objects.get(pk=challenge_id)

        question_form = QuestionForm(request.POST)
        short_text_form = QuestionShortTextForm(request.POST)
        multiple_choice_formset = QuestionMultipleChoiceFormSet(data=request.POST)
        true_false_formset = QuestionTrueFalseFormSet(data=request.POST)

        if question_form.is_valid():

            new_question = question_form.save(commit=False)

            # Set question metadata
            new_question.challenge = challenge
            new_question.created_by = request.user
            new_question.save()

            # Handle type
            # Depending on type, check for different forms and do stuff with them
            if new_question.is_short_text():
                if short_text_form.is_valid():
                    short_text = e_ShortText_Question(question=new_question, correct_text=short_text_form.cleaned_data['correct_text'])
                    short_text.save()
            elif new_question.is_multiple_choice():
                if multiple_choice_formset.is_valid():
                    options = multiple_choice_formset.save(commit=False)
                    for option in options:
                        new_option = e_MultipleChoiceOption_Question(question=new_question, content=option.content, is_correct=option.is_correct)
                        new_option.save()
            elif new_question.is_true_false():
                if true_false_formset.is_valid():
                    options = true_false_formset.save(commit=False)
                    for option in options:
                        new_option = e_TrueFalse_Question(question=new_question, content=option.content, value=option.value)
                        new_option.save()
            
             # Send success message (to be shown in Challenge detail page)
            messages.success(request, 'Your Question has been created successfully.')

            return HttpResponseRedirect(reverse('challenge-manage', args=(challenge_id, )) )
    else:
        question_form = QuestionForm()
        short_text_form = QuestionShortTextForm()
        multiple_choice_formset = QuestionMultipleChoiceFormSet(queryset=e_MultipleChoiceOption_Question.objects.none())
        true_false_formset = QuestionTrueFalseFormSet(queryset=e_TrueFalse_Question.objects.none())
    
    return render(request, 'challenges/question_form.html', {
        'question_form': question_form,
        'short_text_form': short_text_form,
        'multiple_choice_formset': multiple_choice_formset,
        'true_false_formset': true_false_formset,
    })

@login_required
def question_update(request, question_id):
    question = e_Question.objects.get(pk=question_id)

    # Only Event Manager or Platform Admin can do this
    if not context_event_manager_check(request.user, question.challenge.event.context) or is_platform_admin(request.user):
        return HttpResponseRedirect(reverse('challenge-detail', args=[question.challenge.id]))
    
    context = {'question': question,}

    if request.method == 'POST':
        question_form = QuestionUpdateForm(request.POST)
        short_text_form = QuestionShortTextForm(request.POST)
        multiple_choice_formset = QuestionMultipleChoiceFormSet(data=request.POST)
        true_false_formset = QuestionTrueFalseFormSet(data=request.POST)

        if question_form.is_valid():

            # Handle question
            question.content = question_form.cleaned_data['content']
            question.save()

            # Handle type
            if question.is_short_text() and short_text_form.is_valid():
                short_text = e_ShortText_Question.objects.get(question=question)
                short_text.correct_text = short_text_form.cleaned_data['correct_text']
                short_text.save()
            elif question.is_multiple_choice() and multiple_choice_formset.is_valid():
                form_options = multiple_choice_formset.save(commit=False)
                for form_option in form_options:
                    try:
                        # If option exists, update
                        option = e_MultipleChoiceOption_Question.objects.get(pk=form_option.id)
                        option.content = form_option.content
                        option.is_correct = form_option.is_correct
                        option.save()
                    except:
                        # If it doesn't, create a new one
                        new_option = e_MultipleChoiceOption_Question(question=question, content=form_option.content, is_correct=form_option.is_correct)
                        new_option.save()
            elif question.is_true_false() and true_false_formset.is_valid():
                form_options = true_false_formset.save(commit=False)
                for form_option in form_options:
                    try:
                        # If option exists, update
                        option = e_TrueFalse_Question.objects.get(pk=form_option.id)
                        option.content = form_option.content
                        option.value = form_option.value
                        option.save()
                    except:
                        # If it doesn't, create a new one
                        new_option = e_TrueFalse_Question(question=question, content=form_option.content, value=form_option.value)
                        new_option.save()
            
            # Send success message (to be shown in Challenge detail page)
            messages.success(request, 'Your Question has been updated successfully.')

            return HttpResponseRedirect(reverse('challenge-manage', args=(question.challenge.id, )) )
    else:
        question_form = QuestionUpdateForm(instance=question)
        context['question_form'] = question_form
        # Add form to context depending on question type
        if question.is_short_text():
            short_text_form = QuestionShortTextForm(instance=question.short_text_question)
            context['short_text_form'] = short_text_form
        elif question.is_multiple_choice():
            multiple_choice_formset = QuestionMultipleChoiceFormSet(queryset=e_MultipleChoiceOption_Question.objects.filter(question=question))
            context['multiple_choice_formset'] = multiple_choice_formset
        elif question.is_true_false():
            true_false_formset = QuestionTrueFalseFormSet(queryset=e_TrueFalse_Question.objects.filter(question=question))
            context['true_false_formset'] = true_false_formset

    return render(request, 'challenges/question_update_form.html', context)
    

@login_required
def question_delete(request, question_id):
    # question = get_object_or_404(e_Question, pk=question_id)
    question = e_Question.objects.get(pk=question_id)

    # Only Event Manager or Platform Admin can do this
    if not context_event_manager_check(request.user, question.challenge.event.context) or is_platform_admin(request.user):
        return HttpResponseRedirect(reverse('challenge-detail', args=[question.challenge.id]))
    

    # Simply delete (models related to it will be automatically deleted)
    question.delete()
    
    return redirect('challenge-manage', question.challenge.id)



class QuestionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_Question
    template_name = 'challenges/question_form.html'
    form_class = QuestionUpdateForm
    pk_url_kwarg = 'question_id'
    context_object_name = 'question'

    def get_success_url(self):
        return reverse('challenge-manage', args=(self.get_object().challenge.id, ))

    def test_func(self):
        question = e_Question.objects.get(pk=self.kwargs['question_id'])
        # Only Event Manager or Platform Admin can do this
        return context_event_manager_check(self.request.user, question.challenge.event.context) or is_platform_admin(self.request.user)



# TODO: I don't think I'm using this anymore
@login_required
def questionShortTextCreate(request, question_id):
    question = get_object_or_404(e_Question, pk=question_id)

    # TODO:
    # if not question:

    # Only Event Manager or Platform Admin can do this
    if not context_event_manager_check(request.user, question.challenge.event.context) or is_platform_admin(request.user):
        return HttpResponseRedirect(reverse('challenge-detail', args=[question.challenge.id]))
    
    # Create a form instance and populate it with data from the request:
    form = QuestionShortTextForm(request.POST)

    if form.is_valid() and question.challenge.can_manage_questions(): # TODO: AND TYPE == SHORT_TEXT
        # # If object doesn't exist already, create Short Text Question object
        # if not question.short_text_question:
        #     short_text = e_ShortText_Question(question=question, correct_text=form.cleaned_data['correct_text'])
        #     short_text.save()
        # else:
        #     # If it does, then simply edit
        #     question.short_text_question.correct_text = form.cleaned_data['correct_text']
        #     question.short_text_question.save()
        
        try:
            question.short_text_question.correct_text = form.cleaned_data['correct_text']
            question.short_text_question.save()
        except:
            short_text = e_ShortText_Question(question=question, correct_text=form.cleaned_data['correct_text'])
            short_text.save()

        return HttpResponseRedirect(reverse('challenge-manage', args=[question.challenge.id]))
    
    return redirect('challenge-manage', args=[question.challenge.id])