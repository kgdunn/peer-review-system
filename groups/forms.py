from django import forms

class UploadFileForm(forms.Form):
   classlist = forms.FileField(widget=forms.ClearableFileInput(
        attrs={'multiple': False,
               'initial_text': "Please upload a CSV classlist"}))
