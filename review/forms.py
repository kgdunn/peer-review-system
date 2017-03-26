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
    

    def clean_file_upload(self):
        data = self.cleaned_data['file_upload']
        #if "fred@example.com" not in data:
        #    raise forms.ValidationError("You have forgotten about Fred!")

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return data    


class UploadFF(forms.ModelForm):

    learner_ID = forms.TextInput(attrs=None)
    class Meta:
        model= Submission
        fields = ( 'file_upload',)


