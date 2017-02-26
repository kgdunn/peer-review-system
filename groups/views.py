from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt

# Our imports
from utils import generate_random_token
from review.views import get_create_student
from review.models import Person, Course
from .models import Group_Formation_Process, Group, Enrolled
from .forms import UploadFileForm

# Python imports
import re
import datetime
import hashlib
import numpy as np
from random import shuffle

# Logging
import logging
logger = logging.getLogger(__name__)

# SECURITY ISSUES
# Look at https://github.com/Harvard-University-iCommons/django-auth-lti
# Brightspace: https://github.com/open-craft/django-lti-tool-provider
from django.views.decorators.csrf import csrf_exempt
#---------


def starting_point(request):
    """
    Bootstrap code to run on every request.

    Returns a Person instance, the course, and Peer Review (pr) instances.

    """
    person = get_create_student(request)

    course_ID = request.POST.get('context_id', None)
    course = get_object_or_404(Course, label=course_ID)

    group_ID = request.POST.get('resource_link_id', None)
    gID = get_object_or_404(Group_Formation_Process, LTI_id=group_ID)

    if person:
        return person, course, gID
    else:
        return HttpResponse(("You are not registered in this course."))


def randomly_enroll_function(gID):
    """
    Runs the process of randomly enrolling the remaining users.
    """

def handle_uploaded_file(classlist):
    output = []
    classlist_all = classlist.readlines()

    for idx, row in enumerate(classlist_all):

        if idx == 0:
            continue

        row = row.decode().split(',')
        student_number = row[0].strip('#')
        last_name = row[1].strip()
        first_name = row[2].strip()
        email = row[3].strip()

        # Only create student accounts if there is a valid email address:
        if email:
            learner, newbie = Person.objects.get_or_create(
                        email = email,
                        role = 'Learn')
            learner.student_number = student_number
            learner.save()

            if newbie:
                output.append('Added new learner: %s' % learner)


            enrolled = Enrolled(person = learner,
                                group = None,        # this isn't known yet
                                is_enrolled = False) # enrolled when student
                                                     # selects to
            enrolled.save()

            output.append('Enrolled learner: %s' % learner)

    return '\n'.join(output)

#@csrf_exempt
#@xframe_options_exempt
def import_classlist(request):
    """
    Allows the instructor to import a class list. This is used (only) so that
    unallocated students can be assigned, if needed.

    Therefore, importing is only needed if that specific function is required.
    """
    if request.method != 'POST':
        form = UploadFileForm()
        return render(request, 'groups/import_classlist.html', {'form': form})

        #return HttpResponse(("You have reached the Group LTI component "
        #                     "without authorization."))

    #logger.debug('POST = ' + str(request.POST))
    #person_or_error = get_create_student(request)
    #if not(isinstance(person_or_error, Person)):
        #return person_or_error      # Error path if learner does not exist

    #person = person_or_error
    #if person.role == 'Learn':
        #return HttpResponse(("You have reached the Group LTI component "
                             #"without authorization."))

    # Classlist should be exported from Brightspace:
    # Row 1 is ignored
    # OrgDefinedId,	Last Name,	First Name,	Email, ignore rest of columns



    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            output = handle_uploaded_file(request.FILES['classlist'])
            return HttpResponse(str(output))


@csrf_exempt
@xframe_options_exempt
def start_groups(request):
    """
    The group functionality is rendered to the end-learner here.
    """
    if request.method != 'POST':
        return HttpResponse(("You have reached the Group LTI component "
                             "without authorization."))

    # Continue with the main function
    logger.debug('POST = ' + str(request.POST))
    person_or_error, course, gID = starting_point(request)


    if not(isinstance(person_or_error, Person)):
        return person_or_error      # Error path if student does not exist

    learner = person_or_error
    now_time = datetime.datetime.now()

    allow_activity = False
    allow_selfenrol = False
    enrolled_into = []
    group_for_course = []

    if (gID.dt_groups_open_up.replace(tzinfo=None) <= now_time):
        allow_activity = True
        enrolled_into = Enrolled.objects.filter(person=learner)
        #group_for_course = gID

    if (gID.dt_selfenroll_starts.replace(tzinfo=None) <= now_time) and \
        (gID.allow_unenroll):
        allow_selfenrol = True

    if (gID.dt_group_selection_stops.replace(tzinfo=None) <= now_time):
        allow_activity = False
        randomly_enroll_function(gID)

    ctx = {'person': learner,
           'course': course,
           'gID': gID,

          }
    return render(request, 'groups/index.html', ctx)

