from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt


# Our imports
from .models import GradeBook, GradeCategory, GradeItem, LearnerGrade

# Python imports
import io
import csv
import six


# Logging
import logging
logger = logging.getLogger(__name__)

def display_grades(learner, course, request):
    """
    Displays the grades to the student here.
    """
    gradebook = GradeBook.objects.get(course=course)
    categories = GradeCategory.objects.get(gradebook=gradebook)
    gitems = LearnerGrade.objects.filter(learner=learner)

    if learner.role == 'Admin':
        ctx = {'learner': learner,
               'course': course}

        return render(request,
                      'grades/import_grades.html', ctx)

    return HttpResponse('<a href="/grades/import_grades">UPload</a>')

@csrf_exempt
@xframe_options_exempt
def import_edx_gradebook(request):
    """
    Allows the instructor to import a grades list from edX.
    """
    logger.debug("Importing grades: {0}".format(str(request.POST)))
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

    if six.PY2:
        uploaded_file = request.FILES.get('file_upload').read()
        io_string = uploaded_file
    if six.PY3:
        uploaded_file = request.FILES.get('file_upload').read().decode('utf-8')
        io_string = io.StringIO(uploaded_file)
    logger.debug(io_string)

    out = ''
    for row in csv.reader(io_string, delimiter=','):
        print (row)
        out += str(row)

    return HttpResponse('out:' + out)





