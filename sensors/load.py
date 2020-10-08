import os, xlrd, datetime
from .models import e_Sensor, e_SensorObservation
from django.contrib.gis.geos import Point
from datetime import date, time

def run(load_sensors=True, load_observations=True):
    loc = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'sensors_data.xlsx'))
    sensors_file = xlrd.open_workbook(loc)

    if load_sensors:
        sheet = sensors_file.sheet_by_index(0) #where the sheet starts

        for i in range(6, sheet.nrows):
            if(sheet.cell_value == ''):
                break

            sensor = e_Sensor()

            sensor.code = str(int(sheet.cell_value(i,1))) #Eventually this might need to be an int
            sensor.Name = sheet.cell_value(i,2)
            sensor.type = sheet.cell_value(i,3)
            sensor.modalityType = sheet.cell_value(i,4)
            sensor.description = sheet.cell_value(i,5)

            if sheet.cell_value(i,6) == '': sensor.version = None
            else: sensor.version = sheet.cell_value(i,6)
            
            if sheet.cell_value(i,7) == '': sensor.responsibleUser = None 
            else: sensor.responsibleUser = sheet.cell_value(i,7)
            
            sensor.timeZoneAbbreviation = 'GMT'
            sensor.timeZoneOffset = 1
        
            srid = int(sheet.cell_value(i,10))
            coord_str = sheet.cell_value(i,11)
            coords = coord_str.split(',')

            sensor.geom = Point(float(coords[0]), float(coords[1]), srid=srid)

            sensor.save()
            print('Sensor saved!')

    if(load_observations):
        observation_sheet = sensors_file.sheet_by_index(1) #where the sheet starts

        for i in range(6, 100):
            if(observation_sheet.cell_value == ''):
                break

            observation = e_SensorObservation()

            sensor_code = str(int(observation_sheet.cell_value(i,0)))

            observation.sensor = e_Sensor.objects.filter(code=sensor_code).first()
            
            observation.sensorType = 'HydrometricSensor'
            
            raw_time = observation_sheet.cell_value(i,2) #time - float
            #print(raw_time)
            converted_time = xlrd.xldate_as_tuple(raw_time,  sensors_file.datemode)
            #print(converted_time) 
            time_value = time(*converted_time[3:])
            #print(time_value)
            observation.time = time_value
            #observation.time = datetime.now().time()


            raw_date = observation_sheet.cell_value(i,1)
            converted_date = xlrd.xldate_as_tuple(raw_date, sensors_file.datemode)
            observation.date = datetime.datetime(*converted_date)
            #observation.date = datetime.now().today

            if observation_sheet.cell_value(i,3) == '': 
                observation.depth = None
            else: 
                observation.depth = observation_sheet.cell_value(i,3)

            if observation_sheet.cell_value(i,4) == '': 
                observation.discharge = None
            else: 
                observation.discharge = observation_sheet.cell_value(i,4)

            observation.save()
            print('Observation saved!')
