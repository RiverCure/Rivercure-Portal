import os, xlrd
from .models import e_Sensor, e_SensorObservation
import datetime
from datetime import date, time

def run():
    loc = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'sensors_data.xlsx'))
    sensors_file = xlrd.open_workbook(loc)
    sheet = sensors_file.sheet_by_index(1) #where the sheet starts

    for i in range(6, 100):
        if(sheet.cell_value == ''):
            break

        observation = e_SensorObservation()

        sensor_code = str(int(sheet.cell_value(i,0)))

        observation.sensor = e_Sensor.objects.filter(code=sensor_code).first()
        
        observation.sensorType = 'HydrometricSensor'
        
        raw_time = sheet.cell_value(i,2) #time - float
        #print(raw_time)
        converted_time = xlrd.xldate_as_tuple(raw_time,  sensors_file.datemode)
        #print(converted_time) 
        time_value = time(*converted_time[3:])
        #print(time_value)
        observation.time = time_value
        #observation.time = datetime.now().time()

    
        raw_date = sheet.cell_value(i,1)
        converted_date = xlrd.xldate_as_tuple(raw_date, sensors_file.datemode)
        observation.date = datetime.datetime(*converted_date)
        #observation.date = datetime.now().today

        if sheet.cell_value(i,3) == '': 
            observation.depth = None
        else: 
            observation.depth = sheet.cell_value(i,3)

        if sheet.cell_value(i,4) == '': 
            observation.discharge = None
        else: 
            observation.discharge = sheet.cell_value(i,4)
    
        observation.save()
        print('Observation saved!')
