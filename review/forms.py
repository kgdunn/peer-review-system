from django import forms
from .models import Submission

class UploadFileForm_one_file(forms.Form):

    file_upload = forms.FileField(
                widget=forms.ClearableFileInput(
                    attrs={'multiple': False,
                           'initial_text': "Please upload your submission"}))

class UploadFileForm_multiple_file(forms.Form):

    file_upload = forms.FileField(
                widget=forms.ClearableFileInput(
                    attrs={'multiple': True,
                           'initial_text': "Select 1 or more files"}))
    

class UploadFF(forms.ModelForm):

    learner_ID = forms.TextInput(attrs=None)
    class Meta:
        model= Submission
        fields = ( 'file_upload',)


