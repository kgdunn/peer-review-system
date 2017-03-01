from django import forms
from .models import Submission

class UploadFileForm(forms.Form):

    file_submission = forms.FileField(widget=forms.ClearableFileInput(
        attrs={'multiple': False,
               'initial_text': "Please upload your submission"}))



class UploadFF(forms.ModelForm):

    class Meta:
        model= Submission
        fields = ( 'file_upload',)
