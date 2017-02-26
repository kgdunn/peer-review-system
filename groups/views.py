from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt

from utils import generate_random_token

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

@csrf_exempt
@xframe_options_exempt
def start_groups(request):
    return HttpResponse('Creating groups here')