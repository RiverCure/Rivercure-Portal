from datetime import datetime, time

from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, Client

from django.contrib.auth.models import User, AnonymousUser

from context.models import ContextMembership, e_Context, e_ContextEvent, EVENTKIND_CHOICES
from organization.models import Organization, Membership

from ..models import e_Challenge

# Help functions
def setup_with_user(client, user, org):
    """
    Sets up with a client with given user (and '12345' password).
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





def set_session(client, org):
    """
    Set session with given Ort for given Client
    """

    # Set session
    session = client.session
    session.update({ 'organizationCode': org.code })
    session.save()

# 1 class per view

class ChallengeCreateViewTest(TestCase):
    """
    Tests for ChallengeCreateView
    """

    @classmethod
    def setUpTestData(cls):
        # Run once to create objects that aren't going to be modified or changed in any of the methods

        # Set users
        cls.anon_user = AnonymousUser() # Anon user (that is, logged-out user)
        cls.visitor = User.objects.create_user(username='testVisitor', password='12345') # Visitor that belongs to Org
        cls.event_manager = User.objects.create_user(username='testEventManager', password='12345') # Event Manager
        cls.org_manager = User.objects.create_user(username='testOrgManager', password='12345') # Org Manager

        # Set org
        cls.organization = Organization.objects.create(code='testOrg', name='test Organization', type='waterAuthority', create_date=datetime.now(tz=timezone.utc), is_active=True)

        # Create Context
        Membership.objects.create(user=cls.org_manager, organization=cls.organization, access_granted=True, permission='org_manager')
        cls.context = e_Context.objects.create(code='testContext', Name='Test Context', organization=cls.organization, creator=cls.org_manager, create_date=datetime.now(tz=timezone.utc))

        # Give Event Manager permission to event_manager
        ContextMembership.objects.create(user=cls.event_manager, context=cls.context, permission='context_quizManager')

        # Create Event
        cls.event = e_ContextEvent.objects.create(context=cls.context, Name='Test Event', type='flood', state='announced', startTime=time(0,0,0), endTime=time(0,0,0))

        # Save URLs
        cls.login_url = reverse('login')
        cls.url_challenge_create = reverse('challenge-create', args=[cls.event.id])


    # TODO: Can't I just move this into setUpTestData ?
    def setUp(self):
        # Loggin all users into different clients (then use correct client for each)

        # Anonymous
        self.client_anon = Client()

        # Visitor
        self.client_visitor = Client()
        self.client_visitor.login(username=self.visitor.username, password='12345')
        set_session(self.client_visitor, self.organization)

        # Event Manager
        self.client_event_manager = Client()
        self.client_event_manager.login(username=self.event_manager.username, password='12345')
        set_session(self.client_event_manager, self.organization)

        # Org Manager
        self.client_org_manager = Client()
        self.client_org_manager.login(username=self.org_manager.username, password='12345')
        set_session(self.client_org_manager, self.organization)

        

    # def setUp(self):
    #     self.client = Client()

    #     # Set users
    #     self.visitor = User.objects.create_user(username='testVisitor', password='12345') # Visitor that belongs to Org
    #     self.event_manager = User.objects.create_user(username='testEventManager', password='12345') # Event Manager
    #     self.org_manager = User.objects.create_user(username='testOrgManager', password='12345') # Org Manager

    #     # Set org
    #     self.organization = Organization.objects.create(code='testOrg', name='test Organization', type='waterAuthority', create_date=datetime.now(tz=timezone.utc), is_active=True)

    #     # Create Context
    #     Membership.objects.create(user=self.org_manager, organization=self.organization, access_granted=True, permission='org_manager')
    #     self.context = e_Context.objects.create(code='testContext', Name='Test Context', organization=self.organization, creator=self.org_manager, create_date=datetime.now(tz=timezone.utc))

    #     # event_manager needs to be Event Manager in Organization
    #     ContextMembership.objects.create(user=self.event_manager, context=self.context, permission='context_quizManager')

    #     # Create Event
    #     self.event = e_ContextEvent.objects.create(context=self.context, Name='Test Event', type='flood', state='announced', startTime=time(0,0,0), endTime=time(0,0,0))

    #     # Save URLs
    #     self.login_url = reverse('login')
    #     self.url_challenge_create = reverse('challenge-create', args=[self.event.id])

    # def test_view_url_exists_at_desired_location(self):



    def test_anonymous_user_creates_challenge_redirects_to_login(self):
        """
        Anon user is redirected to login page when trying to create a Challenge
        """

        # Test
        response = self.client_anon.post(self.url_challenge_create, {
            'created_by': self.anon_user,
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

        # Test
        response = self.client_visitor.post(self.url_challenge_create, {
            'created_by': self.client_visitor,
            'event': self.event,
            'title': 'Test Challenge',
            'difficulty_level': 'easy',
            'max_participations': 1
        })

        # Assert
        self.assertEquals(response.status_code, 403) # This is forbidden

    
    def test_event_manager_creates_challenge_with_success(self):
        """
        EM successfully creates a Challenge
        """
        print(f'Client is: {self.client_event_manager}')
        print(f'User is: {self.event_manager}')

        # Test
        response = self.client_event_manager.post(self.url_challenge_create, {
            'created_by': self.event_manager,
            'event': self.event,
            'title': 'Test Challenge',
            'difficulty_level': 'easy',
            'max_participations': 1
        })

        challenge = e_Challenge.objects.last()
        expected_redirect_url = reverse('challenge-detail', args=[challenge.id])

        # Assert
        self.assertEquals(response.status_code, 302) # form_valid method from a Create CBV returns 302 code, which is the expected behaviour!
        self.assertRedirects(response, expected_redirect_url, target_status_code=302) # As seen in: https://stackoverflow.com/a/65820856/12387341
        self.assertEquals(challenge.title, 'Test Challenge')