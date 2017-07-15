from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt

# Imports from other applications
# -------------------------------
from review.views import starting_point, recognise_LTI_LMS
from review.models import Person
from stats.views import create_hit

# Logging
import logging
logger = logging.getLogger(__name__)


@csrf_exempt
@xframe_options_exempt
def keyterm_startpage(request):
    if request.method != 'POST' and (len(request.GET.keys())==0):
        return HttpResponse("You have reached the KeyTerms LTI component.")

    person_or_error, course, pr = starting_point(request)

    if not(isinstance(person_or_error, Person)):
        return person_or_error      # Error path if student does not exist

    learner = person_or_error
    logger.debug('Learner entering [pr={0}]: {1}'.format(pr.title, learner))


    create_hit(request, item=learner, event='login', user=learner,)

    LTI_consumer = recognise_LTI_LMS(request)
