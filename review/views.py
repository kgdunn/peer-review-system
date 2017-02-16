from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm

from .models import Person

import logging
logger = logging.getLogger(__name__)
logger.debug('A new call to the views.py file')


# SECURITY ISSUES
# Look at https://github.com/Harvard-University-iCommons/django-auth-lti
# Brightspace: https://github.com/open-craft/django-lti-tool-provider
from django.views.decorators.csrf import csrf_exempt
#---------

# Imaginary function to handle an uploaded file.
def handle_uploaded_file(f):
    with open('/tmp/name.PDF', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

@csrf_exempt
def index(request):
    if request.POST == 'POST':
        return starting_point(request)
    else:
        return HttpResponse(("You have reached the Peer Review LTI component "
                            "without authorization."))

def starting_point(request):
    person = get_create_student(request)
    if person:
        return person
    else:
        return HttpResponse(("You are not registered in this course."))


def get_create_student(request):
    """
    Gets or creates the learner from the POST request.
    """
    logger.debug(str(request.POST))
    if request.POST.contains('ext_d2l_token_digest'):
        name = request.POST['lis_person_name_given']
        email = request.POST['lis_person_contact_email_primary']
        full_name = request.POST['lis_person_name_full']
        user_ID = request.POST['user_id']
    else:
        return None

    learner = Person.objects.get_object_or_404(name=name,
                                               email=email,
                                               full_name=full_name,
                                               user_ID=user_ID)
    return learner

@csrf_exempt
def success(request):
    logger.debug('Success')
    return HttpResponse("You have successfully uploaded")

@csrf_exempt
def index(request):
    logger.debug('Starting')
    if request.method == 'POST':
        logger.debug('POST = ' + str(request.POST))
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['file'])
            return HttpResponseRedirect('/success')
    else:
        form = UploadFileForm()
    return render(request, 'review/upload.html', {'form': form})

