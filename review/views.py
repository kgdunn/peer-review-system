from django.shortcuts import render
from django.http import HttpResponse

# Look at https://github.com/Harvard-University-iCommons/django-auth-lti
# Brightspace: https://github.com/open-craft/django-lti-tool-provider


from django.http import HttpResponseRedirect
from .forms import UploadFileForm

# Imaginary function to handle an uploaded file.
def handle_uploaded_file(f):
    with open('some/file/name.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

#def index(request):
    #if request.POST == 'POST':
        #return HttpResponse("POST request.")
    #else:
        #return HttpResponse(("You have reached the Peer Review LTI component "
                            #"without authorization."))

def success(request):
    return HttpResponse("You have successfully uploaded")

def index(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            #handle_uploaded_file(request.FILES['file'])
            return HttpResponseRedirect('/success')
    else:
        form = UploadFileForm()
    return render(request, 'review/upload.html', {'form': form})

