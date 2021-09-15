from sensors.forms import SensorFileForm, SensorObservationsFileForm
from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from sensors.models import Sensor, SensorClass, SensorClassProperty, SensorObservation, SensorObservationValue
from datetime import datetime, time
from django.contrib.gis.geos.point import Point
from django.db import IntegrityError
from organization.models import Organization
from openpyxl import load_workbook
from organization.authorization import belongs_to_organization
from ..authorization import sensor_edit_permission_check
import string

''' Validate user identity
Security is not a priority. If it was, we would need to check if the user that is uploading is the user that downloaded the file
Some ideas to solve this:
- The sheet is protected and the data in it is valdiated (don't know how much you can tamper with this)
- Save entries on the database with the downloads, who made the download and when
- Authentication
'''
def find_value_from_human_readable(choices, human_readable):
    for value_choice in choices:
        if value_choice[1] == human_readable:
            return value_choice[0]

def get_cell_position(cell):
    return f'{cell.column_letter}{cell.row}'

def sensor_observations_upload(request, sensorId):
    if request.method == 'POST':
        form = SensorObservationsFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['excel_file'].file
            try:
                sensor = get_object_or_404(Sensor, pk=sensorId)
                handle_uploaded_observations_file(f, sensor)
                messages.success(request, 'Observations uploaded successfully')
            except Exception as error:
                if hasattr(error, 'message'):
                    messages.error(request, f'Error parsing observation\'s Excel file: {error.message}')
                else:
                    messages.error(request, f'Error parsing observation\'s Excel file: {error}')

    return redirect('sensor-observation-list', sensorId=sensorId)

def sensor_upload(request):
    if request.method == 'POST':
        form = SensorFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['excel_file'].file
            try:
                handle_uploaded_sensors_file(request.user, f)
                messages.success(request, 'Sensors uploaded successfully')
            except Exception as error:
                if hasattr(error, 'message'):
                    messages.error(request, f'Error parsing sensor\'s Excel file: {error.message}')
                else:
                    messages.error(request, f'Error parsing sensor\'s Excel file: {error}')

    return redirect('sensor-list')

def handle_uploaded_observations_file(file, sensor):
    wb = load_workbook(file)
    ws = wb['Observations']
    properties = SensorClassProperty.objects.filter(sensorClass=sensor.sensorClass).order_by('name')
    cols = 3 + properties.count() # the 3 are the mandatory, fixed, ones
    max_column = list(string.ascii_uppercase)[cols - 1]
    severity_choices = SensorObservation._meta.get_field('severity').choices

    def validate_data(idx, cell):
        value = cell.value
        position = get_cell_position(cell)
        if idx == 0: # date
            try:
                return value.date()
            except Exception as ex:
                raise Exception(f'[{position}] Couldn\'t convert date format')
        elif idx == 1: # time
            try:
                return value
            except:
                raise Exception(f'[{position}] Couldn\'t convert time format')
        elif idx == 2: # severity
            choices_full_name = [ choice[1] for choice in severity_choices ]
            if value not in choices_full_name:
                raise Exception(f'[{position}] Please introduce a valid severity option')
            return find_value_from_human_readable(severity_choices, value)
        else: # sensor property values
            prop = properties[idx - 3]
            if prop.isOptional == False and value == None:
                raise Exception(f'[{position}] Please introduce a value, since the property is mandatory')

            if prop.type == 'number':
                try:
                    return float(value)
                except:
                    if not prop.isOptional:
                        raise Exception(f'[{position}] Please introduce a valid number')
            else:
                if value == None and not prop.isOptional:
                    raise Exception(f'[{position}] This field is mandatory')
                else:
                    return '' if value == None else value

    def save_observation(data):
        try:
            with transaction.atomic():
                obs = SensorObservation.objects.filter(date=data[0], time=data[1], sensor=sensor)
                if obs.exists() and obs.count() == 1:
                    # Update
                    obs.update(severity=data[2])
                    for idx, value in enumerate(data[3:]): # sensor property (variable) fields
                        if value != '' and value != None:
                            obs_v = SensorObservationValue.objects.filter(property=properties[idx], observation=obs[0])
                            if obs_v.exists():
                                obs_v.update(value=value)
                            else:
                                SensorObservationValue.objects.create(property=properties[idx], observation=obs[0], value=value)
                else:
                    obs = SensorObservation.objects.create(date=data[0], time=data[1], sensor=sensor, severity=data[2])
                    for idx, value in enumerate(data[3:]): # sensor property (variable) fields
                        if value != '' and value != None:
                            SensorObservationValue.objects.create(property=properties[idx], observation=obs, value=value)
        
        except Exception as error:
            print(error)
            if 'duplicate key value violates unique constraint' not in error.__str__():
                raise Exception('Something happened creating the observations. Please save this file and contact the admin')

    # Tells which fields are optional (True or False)
    optional_fields = list(map(lambda el: el.fill.bgColor.rgb == 'FFFFFF00', ws['A1':f'{max_column}1'][0]))
    observation_fields = list()
    
    for row in ws.iter_rows(min_row=2, max_col=cols, max_row=ws.max_row):
        for idx, cell in enumerate(row):
            if cell.value == None and optional_fields[idx] == False:
                raise Exception(f'[{get_cell_position(cell)}] Please introduce data in this mandatory field')
            
            observation_fields.append(validate_data(idx, cell))

        save_observation(observation_fields)
        observation_fields.clear()

def handle_uploaded_sensors_file(user, file):
    wb = load_workbook(file)
    ws = wb['Sensors']
    state_choices = Sensor._meta.get_field('state').choices

    def validate_data(idx, cell):
        value = cell.value
        position = get_cell_position(cell)
        if idx == 0: # sensor class
            try:
                sensorClass = SensorClass.objects.get(code=value)
                org = sensorClass.organization
                if belongs_to_organization(user, org) == False:
                    raise Exception(f'[{position}] You don\'t have access to the selected sensor class or it doesn\'t exist')
                return sensorClass
            except:
                raise Exception(f'[{position}] You don\'t have access to the selected sensor class or it doesn\'t exist')
        elif idx == 1: # code
            return value
        elif idx == 2: # name
            return value
        elif idx == 3: # state
            choices_state = [ choice[1] for choice in state_choices ]
            if value not in choices_state:
                raise Exception(f'[{position}] Please introduce a valid state option')
            return find_value_from_human_readable(state_choices, value)
        elif idx == 4: # description
            return value if value else ''
        elif idx == 5: # is public
            if value != None and value != 'Yes' and value != 'No':
                raise Exception(f'[{position}] Please select either Yes or No')
            return True if value == 'Yes' or value == None else False
        elif idx == 6: # local
            try:
                point_values = value.split(',')
                point = Point(float(point_values[0]), float(point_values[1]), srid=3763)
                return point
            except:
                raise Exception(f'[{position}] Please enter a valid coordinate for a point')

    def save_sensor(data):
        try:
            try:
                sensor = Sensor.objects.filter(code=data[1]) # returns exception if object doesn't exist
                hasPerm = sensor_edit_permission_check(user, sensor[0])
                if hasPerm:
                    sensor.update(sensorClass=data[0], code=data[1], name=data[2], state=data[3], description=data[4], isPublic=data[5], local=data[6])
                else:
                    raise Exception(f'[{data[1]}] Can\'t introduce that sensor because a sensor with that code already exists and you don\'t have permission to edit it')
            except:
                Sensor.objects.create(sensorClass=data[0], code=data[1], name=data[2], state=data[3], description=data[4], isPublic=data[5], local=data[6])

        except Exception as error:
            if 'duplicate key value violates unique constraint' not in error.__str__():
                raise Exception('Something happened creating the sensors. Please save this file and contact the admin')

    # Tells which fields are optional (True or False)
    optional_fields = list(map(lambda el: el.fill.bgColor.rgb == 'FFFFFF00', ws['A1':'G1'][0]))
    sensor_fields = list()
    for row in ws.iter_rows(min_row=2, max_col=7, max_row=ws.max_row):
        for idx, cell in enumerate(row):
            if cell.value == None and optional_fields[idx] == False:
                raise Exception(f'[{get_cell_position(cell)}] Please introduce data in this mandatory field')
            
            sensor_fields.append(validate_data(idx, cell))

        save_sensor(sensor_fields)
        sensor_fields.clear()