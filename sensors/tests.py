from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import Client, TestCase
from django.test.utils import override_settings
from organization.models import Membership, Organization
from sensors.models import Sensor, SensorCategory, SensorClass, SensorClassProperty, SensorObservation, SensorObservationValue
from datetime import datetime
from django.utils import timezone


class TestEndpoints(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.organization = Organization.objects.create(name='testOrganizationo', type='waterAuthority', create_date=datetime.now(tz=timezone.utc), is_active=True)
        # Set session
        session = self.client.session
        session.update({
            'organizationName': self.organization.name
        })
        session.save()
        Membership.objects.create(user=self.user, organization=self.organization, access_granted=True, permission='org_manager')

        category = SensorCategory.objects.create(name='testCategoryo')
        self.sensorClass = SensorClass.objects.create(code='hydrometricSensor', name='hydrometricSensor', state='active',  modality='PhysicalFixed', category=category, organization=self.organization)
        self.prop = SensorClassProperty.objects.create(code='propTest', name='prop test', type='number', isOptional=False, sensorClass=self.sensorClass)
        self.sensor = Sensor.objects.create(code='sensorCoura', name='sensorCoura', state='active', isPublic=True, local=Point(5, 23), sensorClass=self.sensorClass)

    def test_sensor_views(self):
        sensorId = self.sensor.pk

        response = self.client.get('/sensors/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/sensors/others/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/sensors/new/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/{sensorId}/update/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/{sensorId}/geo-update/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/{sensorId}/delete/')
        self.assertEqual(response.status_code, 200)

    def test_sensor_class_views(self):
        organizationId = self.organization.pk
        sensorClassId = self.sensorClass.pk

        response = self.client.get(f'/sensors/sensor-class/{organizationId}')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/sensor-class/{organizationId}/new')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/sensor-class/{sensorClassId}/detail')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/sensor-class/{sensorClassId}/update')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/sensor-class/{sensorClassId}/delete')
        self.assertEqual(response.status_code, 200)

    def test_sensor_class_property_views(self):
        sensorClassId = self.sensorClass.pk
        propertyId = self.prop.pk

        response = self.client.get(f'/sensors/sensor-class/{sensorClassId}/property/list')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/sensor-class/{sensorClassId}/property/new')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/sensor-class/{sensorClassId}/property/{propertyId}/detail')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/sensor-class/{sensorClassId}/property/{propertyId}/update')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/sensor-class/{sensorClassId}/property/{propertyId}/delete')
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=True)
    def test_observations_views(self):
        sensorId = self.sensor.pk
        now = datetime.now()
        observation = SensorObservation.objects.create(date=now, time=now.time(), severity='ok', sensor=self.sensor)
        SensorObservationValue.objects.create(property=self.prop, observation=observation, value='abc')

        response = self.client.get(f'/sensors/{sensorId}/observation/new/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/{sensorId}/observations/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/{sensorId}/observation/{observation.pk}')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/{sensorId}/observation/{observation.pk}/update', follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/sensors/{sensorId}/observation/{observation.pk}/delete', follow=True)
        self.assertEqual(response.status_code, 200)
