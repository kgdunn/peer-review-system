from django import forms

class UploadFileForm(forms.Form):

    file_submission = forms.FileField(widget=forms.ClearableFileInput(
        attrs={'multiple': False,
               'initial_text': "Please upload your submission"}))
