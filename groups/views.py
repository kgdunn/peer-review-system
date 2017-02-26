from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt

# Our imports
from utils import generate_random_token
from review.views import get_create_student
from review.models import Person, Course
from .models import Group_Formation_Process

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


@csrf_exempt
@xframe_options_exempt
def start_groups(request):
    """
    The group functionality is rendered to the end-learner here.
    """
    if request.method == 'POST':
        logger.debug('POST = ' + str(request.POST))
        person_or_error, course, gID = starting_point(request)


        if not(isinstance(person_or_error, Person)):
            return person_or_error      # Error path if student does not exist
        else:
            learner = person_or_error
            now_time = datetime.datetime.now()

            # Set bools
            # Set variables depeding on the timing information
            # Render template

            #if (pr.dt_submissions_open_up.replace(tzinfo=None) <= now_time) \
            #    and (pr.dt_submission_deadline.replace(tzinfo=None)>now_time):
            #    allow_submit = True

            # if after cutoff:
            # run "randomly_enroll_function(), if required"


            ctx = {'person': learner,
                   'course': course,
                  }
            return render(request, 'groups/index.html', ctx)

    else:
        return HttpResponse(("You have reached the Group LTI component "
                             "without authorization."))
