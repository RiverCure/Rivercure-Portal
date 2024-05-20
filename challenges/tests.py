from datetime import datetime, time

from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, Client

from django.contrib.auth.models import User

from context.models import ContextMembership, e_Context, e_ContextEvent, EVENTKIND_CHOICES
from organization.models import Organization, Membership

from .models import e_Challenge


# Create your tests here.
class TestViews(TestCase):

    def setUp(self):
        self.client = Client()

        # Set user
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.organization = Organization.objects.create(code='testOrg', name='test Organization', type='waterAuthority', create_date=datetime.now(tz=timezone.utc), is_active=True)

        # Set session
        session = self.client.session
        session.update({ 'organizationCode': self.organization.code })
        session.save()

        # Create Context
        org_manager = User.objects.create_user(username='orgManager', password='12345')
        Membership.objects.create(user=org_manager, organization=self.organization, access_granted=True, permission='org_manager')
        self.context = e_Context.objects.create(code='testContext', Name='Test Context', organization=self.organization, creator=org_manager, create_date=datetime.now(tz=timezone.utc))

        # User needs to be Event Manager in Organization
        ContextMembership.objects.create(user=self.user, context=self.context, permission='context_eventManager')

        # Create Event
        self.event = e_ContextEvent(context=self.context, Name='Test Event', type='flood', state='announced', startTime=time(0,0,0), endTime=time(0,0,0))


    
    def test_challenge_create_creates_new_challenge(self):
        # Set up

        # Test
        response = self.client.post(reverse('challenge-create', args=[self.event.id]), {
            'created_by': self.user,
            'event': self.event,
            'title': 'Test Challenge',
            'difficulty_level': 'easy',
            'max_participations': 1
        })
        print(response)

        # Assert
        self.assertEquals(response.status_code, 200)