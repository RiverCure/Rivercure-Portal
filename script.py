import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rivercureproject.settings")
django.setup()
from context.models import e_ContextBoundaryLine

outputs = e_ContextBoundaryLine.objects.filter(type="Characteristics")
for obj in outputs:
	obj.type = "Outlet"
	obj.criteria = "Characteristics"
	obj.save()

