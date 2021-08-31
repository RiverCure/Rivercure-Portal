from sensors.forms import SensorFileForm, SensorObservationsFileForm
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from sensors.models import Sensor, SensorObservation
from datetime import datetime, time
import xlrd
from django.contrib.gis.geos.point import Point
from django.db import IntegrityError
from organization.models import Organization

def sensor_observations_upload(request, pk):
    if request.method == 'POST':
        form = SensorObservationsFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['excel_file'].read()
            try:
                print(request.FILES['excel_file'])
                handle_uploaded_observations_file(f)
                messages.success(request, 'Observations uploaded successfully')
            except Exception as error:
                if hasattr(error, 'message'):
                    messages.error(request, f'Error parsing observation\'s Excel file: {error.message}')
                else:
                    messages.error(request, f'Error parsing observation\'s Excel file: {error}')

            return redirect('sensor-observation-list', pk=pk)

    return redirect('sensor-observation-list', pk=pk)

def sensor_upload(request):
    if request.method == 'POST':
        form = SensorFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['excel_file'].read()
            # Sensors
            try:
                handle_uploaded_sensors_file(f)
                messages.success(request, 'Sensors uploaded successfully')
            except Exception as error:
                if hasattr(error, 'message'):
                    messages.error(request, f'Error parsing sensor\'s Excel file: {error.message}')
                else:
                    messages.error(request, f'Error parsing sensor\'s Excel file: {error}')
            # Observations
            try:
                handle_uploaded_observations_file(f)
                messages.success(request, 'Observations uploaded successfully')
            except Exception as error:
                if hasattr(error, 'message'):
                    messages.error(request, f'Error parsing observation\'s Excel file: {error.message}')
                else:
                    messages.error(request, f'Error parsing observation\'s Excel file: {error}')


            return HttpResponseRedirect('/sensors/')

    return HttpResponseRedirect('/sensors/')

def handle_uploaded_observations_file(file):
    sensors_file = xlrd.open_workbook(file_contents=file)
    observation_sheet = sensors_file.sheet_by_index(1)
    
    for i in range(6, observation_sheet.nrows):
        if(observation_sheet.cell_value(i,0) == ''):
            break
        
        observation = SensorObservation()

        check_float = isinstance(observation_sheet.cell_value(i,0), float)
        if check_float:
            print(observation_sheet.cell_value(i,0))
            if int(observation_sheet.cell_value(i,0)) == observation_sheet.cell_value(i,0):
                sensor_code = str(int(observation_sheet.cell_value(i,0)))
                observation.sensor = Sensor.objects.filter(code=sensor_code).first()
            else:
                sensor_code = str(observation_sheet.cell_value(i,0))
                observation.sensor = Sensor.objects.filter(code=sensor_code).first()
        
        else:
            sensor_code = str(observation_sheet.cell_value(i,0))
            observation.sensor = Sensor.objects.filter(code=sensor_code).first()
        
        observation.sensorType = 'HydrometricSensor'
        
        raw_time = observation_sheet.cell_value(i,2) #time - float
        converted_time = xlrd.xldate_as_tuple(raw_time,  sensors_file.datemode)
        time_value = time(*converted_time[3:])
        observation.time = time_value

        raw_date = observation_sheet.cell_value(i,1)
        converted_date = xlrd.xldate_as_tuple(raw_date, sensors_file.datemode)
        observation.date = datetime.datetime(*converted_date)

        if observation_sheet.cell_value(i,3) == '': 
            observation.depth = None
        else: 
            observation.depth = observation_sheet.cell_value(i,3)

        if observation_sheet.cell_value(i,4) == '': 
            observation.discharge = None
        else: 
            observation.discharge = observation_sheet.cell_value(i,4)
        try:
            observation.save()
            print('Observation saved!')
        except Exception as error:
            if type(error) is not IntegrityError: # if it isn't an error of duplicate entry in database, raise it
                raise Exception(error)
                return



def handle_uploaded_sensors_file(file):
    sensors_file = xlrd.open_workbook(file_contents=file)
    sensors_sheet = sensors_file.sheet_by_index(0)
    
    for i in range(6, sensors_sheet.nrows):
        if(sensors_sheet.cell_value == ''):
            break

        sensor = Sensor()

        check_float = isinstance(sensors_sheet.cell_value(i,0), float)
        if check_float:
            if int(sensors_sheet.cell_value(i,0)) == sensors_sheet.cell_value(i,0):
                sensor_code = str(int(sensors_sheet.cell_value(i,0)))
            else:
                sensor_code = str(sensors_sheet.cell_value(i,0))
        
        else:
            sensor_code = str(sensors_sheet.cell_value(i,0))

        sensor.code = sensor_code
        sensor.Name = sensors_sheet.cell_value(i,1)
        try:
            sensor.organization = Organization.objects.get(name=sensors_sheet.cell_value(i,2))
        except:
            raise Exception('That organization doesn\'t exist')
            return

        sensor.type = sensors_sheet.cell_value(i,3)
        sensor.modalityType = sensors_sheet.cell_value(i,4)
        sensor.description = sensors_sheet.cell_value(i,5)

        if sensors_sheet.cell_value(i,6) == '': sensor.version = None
        else: sensor.version = sensors_sheet.cell_value(i,6)
        
        if sensors_sheet.cell_value(i,7) == '': sensor.responsibleUser = None 
        else: sensor.responsibleUser = sensors_sheet.cell_value(i,7)
        
        sensor.timeZoneAbbreviation = 'GMT'
        sensor.timeZoneOffset = 1

        if sensors_sheet.cell_value(i,10) == '': srid = 3763
        else: srid = int(sensors_sheet.cell_value(i,10))

        coord_str = sensors_sheet.cell_value(i,11)
        coords = coord_str.split(',')

        sensor.geom = Point(float(coords[0]), float(coords[1]), srid=srid)

        sensor.save()
        print('Sensor saved!')