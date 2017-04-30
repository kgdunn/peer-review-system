from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt


# Our imports
from .models import GradeBook, GradeCategory, GradeItem, LearnerGrade
from review.models import Person

# Python imports
import io
import csv
import six


# Logging
import logging
logger = logging.getLogger(__name__)

def display_grades(learner, course, pr, request):
    """
    Displays the grades to the student here.
    """
    gradebook = GradeBook.objects.get(course=course)
    categories = GradeCategory.objects.get(gradebook=gradebook)
    gitems = LearnerGrade.objects.filter(learner=learner)

    if learner.role == 'Admin':
        ctx = {'learner': learner,
               'course': course,
               'pr': pr}

        return render(request,
                      'grades/import_grades.html', ctx)

    return HttpResponse('Grades will be displayed here.')

@csrf_exempt
@xframe_options_exempt
def import_edx_gradebook(request):
    """
    Allows the instructor to import a grades list from edX.
    """

    logger.debug("Importing grades:")
    SKIP_FIELDS = [
        "Student ID",
        "Email",
        "Username",
        "Grade",
        "Enrollment Track",
        "Verification Status",
        "Certificate Eligible",
        "Certificate Delivered",
        "Certificate Type"]

    if request.method != 'POST':
        return HttpResponse(('Grades cannot be uploaded directly. Please upload'
                             ' the grades via edX.'))

    if request.method == 'POST' and request.FILES.get('file_upload', None):
        pass
    else:
        return HttpResponse('A file was not uploaded, or a problem occurred.')

    from review.views import starting_point
    person_or_error, course, pr = starting_point(request)

    if not(isinstance(person_or_error, Person)):
        return person_or_error      # Error path if student does not exist

    learner = person_or_error

    if six.PY2:
        uploaded_file = request.FILES.get('file_upload').readlines()
        io_string = uploaded_file
    if six.PY3:
        uploaded_file = request.FILES.get('file_upload').read().decode('utf-8')
        io_string = io.StringIO(uploaded_file)
    logger.debug(io_string)

    out = ''
    for row in csv.reader(io_string, delimiter=','):
        out += str(row)



    return HttpResponse('out:' + out)





