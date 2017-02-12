from django import forms

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)

    file = forms.FileField()
    #file = forms.FileField(widget=forms.ClearableFileInput(
    #    attrs={'multiple': False,
    #           'initial_text': "Please upload a file"}))

