# from django.contrib.auth.models import User
# from django.test import Client, TestCase
# from django.test.utils import override_settings
# from context.models import e_Context
# from organization.models import Membership, Organization
# from datetime import datetime
# from django.utils import timezone


# class TestEndpoints(TestCase):
    
#     def setUp(self):
#         self.client = Client()
#         self.user = User.objects.create_user(username='testuser', password='12345')
#         self.client.login(username='testuser', password='12345')
#         self.organization = Organization.objects.create(name='testOrganizationo', type='waterAuthority', create_date=datetime.now(tz=timezone.utc), is_active=True)
#         # Set session
#         session = self.client.session
#         session.update({
#             'organizationCode': self.organization.code
#         })
#         session.save()
#         Membership.objects.create(user=self.user, organization=self.organization, access_granted=True, permission='org_manager')
#         self.context = e_Context.objects.create(code='testCtx', Name='test Ctx', organization=self.organization, creator=self.user, create_date=datetime.now(tz=timezone.utc), isPublic=True)

#     @override_settings(DEBUG=True)
#     def test_context_views(self):
#         contextCode = self.context.code

#         response = self.client.get('/contexts/')
#         self.assertEqual(response.status_code, 200)

#         response = self.client.get('/contexts/new/')
#         self.assertEqual(response.status_code, 200)

#         response = self.client.get('/contexts/others/')
#         self.assertEqual(response.status_code, 200)

#         response = self.client.get(f'/contexts/{contextCode}/')
#         self.assertEqual(response.status_code, 200)

#         response = self.client.get(f'/contexts/{contextCode}/update/')
#         self.assertEqual(response.status_code, 200)

#         response = self.client.get(f'/contexts/{contextCode}/delete/')
#         self.assertEqual(response.status_code, 200)

#         response = self.client.get(f'/contexts/{contextCode}/manage/')
#         self.assertEqual(response.status_code, 200)

#         response = self.client.get(f'/contexts/{contextCode}/upload/')
#         self.assertEqual(response.status_code, 200)