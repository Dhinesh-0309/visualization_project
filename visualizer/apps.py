# visualizer/forms.py
from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()  # The file field to upload a CSV
