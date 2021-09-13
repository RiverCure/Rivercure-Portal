from sensors.models import SensorCategory

def create_default():
    SensorCategory.objects.create(name='Hydrometric Sensor')
    SensorCategory.objects.create(name='Weather Sensor')
    SensorCategory.objects.create(name='Social Network Scanner')

def run():
    create_default()