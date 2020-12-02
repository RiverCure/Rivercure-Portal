from django import forms


class SensorObservationsFileForm(forms.Form):
    excel_file = forms.FileField()
