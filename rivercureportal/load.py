import os
from django.contrib.gis.utils import LayerMapping
from .models import e_District, e_Municipality, e_Parish, e_HydroFeature


class CustomLayerMapping(LayerMapping):
    def __init__(self, *args, **kwargs):
        self.custom = kwargs.pop('custom', {})
        super(CustomLayerMapping, self).__init__(*args, **kwargs)

    def feature_kwargs(self, feature):
        kwargs = super(CustomLayerMapping, self).feature_kwargs(feature)
        kwargs.update(self.custom)
        return kwargs

# Auto-generated `LayerMapping` dictionary for Portugal_Districts model
districts_mapping = {
    'code': 'Di',
    'Name': 'District',
    'geom': 'MULTIPOLYGON',
}

# Auto-generated `LayerMapping` dictionary for Portugal_Municipalities model
municipalities_mapping = {
    'code': 'Dico',
    'Name': 'Municipali',
    'district': {'code': 'Di'},
    'geom': 'MULTIPOLYGON',
}

# Auto-generated `LayerMapping` dictionary for Portugal_Parishes model
parishes_mapping = {
    'code': 'Dicofre',
    'Name': 'Parish',
    'municipality': {'code': 'Dico'},
    'geom': 'MULTIPOLYGON',
}

hydrofeature_mapping = {
    'code': 'Name',
    'Name': 'Descriptio',
    #'type': 'RiverBasin',
    'area': 'Shape_Area',
    'length': 'Shape_Leng',
    'geom': 'MULTIPOLYGON',
}


district_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'data', 'Districts/Portugal_Districts.shp'),
)

municipality_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'data', 'Municipalities/Portugal_Municipalities.shp'),
)

parish_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'data', 'Parishes/Portugal_Parishes.shp'),
)

hydrofeature_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'data', 'Hydro_Features/Subbasin.shp'),
)

def run(verbose=True, options=[True, True, True, True]):
    if options[0]: #Districts migration
        districts = LayerMapping(e_District, district_shp, districts_mapping, transform=False)
        districts.save(strict=True, verbose=verbose)

    if options[1]: #Municipalities migration
        municipalities = LayerMapping(e_Municipality, municipality_shp, municipalities_mapping, transform=False)
        municipalities.save(strict=True, verbose=verbose)

    if options[2]: #Parishies migration
        parishies = LayerMapping(e_Parish, parish_shp, parishes_mapping, transform=False)
        parishies.save(strict=True, verbose=verbose)

    if options[3]: #Hydro Features migration
        parishies = CustomLayerMapping(e_HydroFeature, hydrofeature_shp, hydrofeature_mapping, custom={'type': 'RiverBasin'}, transform=False)
        parishies.save(strict=True, verbose=verbose)

