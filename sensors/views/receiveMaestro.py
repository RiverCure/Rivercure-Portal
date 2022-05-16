# Receives data from Maestro
import json
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from sensors.models import Sensor, SensorClassProperty, SensorObservation, SensorObservationValue

def check_if_exits(sensor, date, time, depth, url):
    try:
        obs = SensorObservation.objects.get(sensor=sensor, date=date, time=time)
    except:
        return False

    try:
        property_depth = obs.sensorobservationvalue_set.get(property__code='depth')
        property_url = obs.sensorobservationvalue_set.get(property__code='url')
    except:
        return False

    if property_depth.value == depth or property_url.value == url:
        return True

    return False

@csrf_exempt
def receive(request):
    if request.method != "POST" or request.body == b'' or request.body == '' or request.META['CONTENT_TYPE'] != 'application/json':
        return HttpResponseBadRequest()

    try:
        sensor = Sensor.objects.get(code='AguedaSocialSensor')
        depth_property = SensorClassProperty.objects.get(code='depth', sensorClass=sensor.sensorClass)
        url_property = SensorClassProperty.objects.get(code='url', sensorClass=sensor.sensorClass)
    except:
        return HttpResponseServerError()

    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        flood_depth = body['Flood depth']

        for image in flood_depth:
            url = image['preview_url']
            depth = image['result']
            datetime = image['datetime']
            if not datetime or datetime == '':
                continue
            print(datetime)

            date, time = datetime.split()
            date = date.replace(':', '-') # dates come in YYYY:MM:DD and we transform to YYYY-MM-DD
            # Check if exists
            exists = check_if_exits(sensor, date, time, depth, url)
            if not exists:
                obs = SensorObservation.objects.create(sensor=sensor, severity='ok', date=date, time=time)
                SensorObservationValue.objects.create(property=depth_property, observation=obs, value=depth).save()
                SensorObservationValue.objects.create(property=url_property, observation=obs, value=url).save()
                obs.save()
    
    except Exception as ex:
        print(ex)
        return HttpResponseBadRequest()

    return HttpResponse(status=200)