from datetime import datetime, time

from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, Client

from django.contrib.auth.models import User, AnonymousUser

from context.models import ContextMembership, e_Context, e_ContextEvent, EVENTKIND_CHOICES
from organization.models import Organization, Membership

from .models import e_Challenge

# Help functions
def setup_with_user(client, user, org):
    """
    Sets up with a client with given user. Always uses '12345' password.
    Sets session with given organization.
    """
    # Set client
    client.login(username=user.username, password='12345')

    # Set session
    session = client.session
    session.update({ 'organizationCode': org.code })
    session.save()
    
def cleanup(client):
    """
    Logs client out.
    """
    client.logout()

# 1 class per view

class ChallengeCreateView(TestCase):

    def setUp(self):
        self.client = Client()

        # Set users
        self.visitor = User.objects.create_user(username='testVisitor', password='12345') # Visitor that belongs to Org
        self.event_manager = User.objects.create_user(username='testEventManager', password='12345') # Event Manager
        self.org_manager = User.objects.create_user(username='testOrgManager', password='12345') # Org Manager

        # Set org
        self.organization = Organization.objects.create(code='testOrg', name='test Organization', type='waterAuthority', create_date=datetime.now(tz=timezone.utc), is_active=True)

        # Create Context
        Membership.objects.create(user=self.org_manager, organization=self.organization, access_granted=True, permission='org_manager')
        self.context = e_Context.objects.create(code='testContext', Name='Test Context', organization=self.organization, creator=self.org_manager, create_date=datetime.now(tz=timezone.utc))

        # event_manager needs to be Event Manager in Organization
        ContextMembership.objects.create(user=self.event_manager, context=self.context, permission='context_eventManager')

        # Create Event
        self.event = e_ContextEvent.objects.create(context=self.context, Name='Test Event', type='flood', state='announced', startTime=time(0,0,0), endTime=time(0,0,0))

        # Save URLs
        self.login_url = reverse('login')
        self.url_challenge_create = reverse('challenge-create', args=[self.event.id])


    def test_anonymous_user_creates_challenge_redirects_to_login(self):
        """
        Anon user is redirected to login page when trying to create a Challenge
        """
        # Set up
        anon_client = Client()
        anon_user = AnonymousUser()

        # Test
        response = anon_client.post(self.url_challenge_create, {
            'created_by': anon_user,
            'event': self.event,
            'title': 'Test Challenge',
            'difficulty_level': 'easy',
            'max_participations': 1
        })

        # Assert
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, self.login_url + f'?next={self.url_challenge_create}') # Check if it redirects to a login page
    

    def test_visitor_creates_challenge_redirects_to_login(self):
        """
        User that is not an Event Manager for that Context or a Platform Admin is redirected to login page when trying to create a Challenge
        """
        # Set up
        setup_with_user(self.client, self.visitor, self.organization)

        # Test
        response = self.client.post(self.url_challenge_create, {
            'created_by': self.visitor,
            'event': self.event,
            'title': 'Test Challenge',
            'difficulty_level': 'easy',
            'max_participations': 1
        })

        # Clean up
        cleanup(self.client)

        # Assert
        self.assertEquals(response.status_code, 403) # This is forbidden

    
    def test_event_manager_creates_challenge_with_success(self):
        """
        EM successfully creates a Challenge
        """
        # Set up
        setup_with_user(self.client, self.event_manager, self.organization)

        # Test
        response = self.client.post(self.url_challenge_create, {
            'created_by': self.event_manager,
            'event': self.event,
            'title': 'Test Challenge',
            'difficulty_level': 'easy',
            'max_participations': 1
        })

        # Clean up
        cleanup(self.client)

        challenge = e_Challenge.objects.last()
        expected_redirect_url = reverse('challenge-detail', args=[challenge.id])

        # Assert
        self.assertEquals(response.status_code, 302) # form_valid method from a Create CBV returns 302 code, which is the expected behaviour!
        self.assertRedirects(response, expected_redirect_url, target_status_code=302) # As seen in: https://stackoverflow.com/a/65820856/12387341
        self.assertEquals(challenge.title, 'Test Challenge')