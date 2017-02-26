from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt

# Our imports
from utils import generate_random_token
from review.views import get_create_student
from review.models import Person, Course
from .models import Group_Formation_Process, Group, Enrolled

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

def import_classlist(request):
    """
    Allows the instructor to import a class list
    """

    if request.method != 'POST':
        return HttpResponse(("You have reached the Group LTI component "
                             "without authorization."))

    logger.debug('POST = ' + str(request.POST))
    person_or_error, course, gID = starting_point(request)
    if not(isinstance(person_or_error, Person)):
        return person_or_error      # Error path if learner does not exist

    person = person_or_error
    if person.role == 'Learn':
        return HttpResponse(("You have reached the Group LTI component "
                             "without authorization."))




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

