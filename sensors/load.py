import os, xlrd
from .models import e_Sensor
from django.contrib.gis.geos import Point

def run():
    loc = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'sensors_data.xlsx'))
    sensors_file = xlrd.open_workbook(loc)
    sheet = sensors_file.sheet_by_index(0) #where the sheet starts

    for i in range(6, sheet.nrows):
        if(sheet.cell_value == ''):
            break

        sensor = e_Sensor()

        sensor.code = sheet.cell_value(i,1)
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
