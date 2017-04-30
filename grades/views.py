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
import datetime
from collections import defaultdict

# Logging
import logging
logger = logging.getLogger(__name__)

def display_grades(learner, course, pr, request):
    """
    Displays the grades to the student here.
    """
    gradebook = GradeBook.objects.get(course=course)
    grades = {}
    if learner.role == 'Admin':
        ctx = {'learner': learner,
               'course': course,
               'pr': pr}

        return render(request,
                      'grades/import_grades.html', ctx)

    categories = GradeCategory.objects.filter(gradebook=gradebook)\
                                                            .order_by('order')

    for gcat in categories:
        if gcat.gradeitem_set.all().count() == 0:
            continue

        items = gcat.gradeitem_set.all().order_by('order')
        for item in items:
            grade = LearnerGrade.objects.filter(learner=learner, gitem=item)
            if grade.count() == 0:
                pass
            else:
                key = gcat.order + item.order/1000.0
                grades[key] = grade[0]

    if six.PY2:
        ctx = {'grades': sorted(grades.iteritems())}
    elif six.PY3:
        ctx = {'grades': sorted(grades.items())}

    ctx['course'] = course
    ctx['gradebook'] = gradebook

    return render(request, 'grades/learner_grades.html', ctx)

@csrf_exempt
@xframe_options_exempt
def import_edx_gradebook(request):
    """
    Allows the instructor to import a grades list from edX.

    Improvements:
    * create a "Person" profile for students that in the CSV file, but not yet
      in the DB.
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
        "Certificate Type",
        "(Avg)",   # <--- special case: skip calculated columns
    ]

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
    reader = csv.reader(io_string, delimiter=',')
    columns = defaultdict(int)
    for row in reader:
        if reader.line_num == 1:
            order = 0
            for idx, col in enumerate(row):
                invalid = False
                for skip in SKIP_FIELDS:
                    if col.endswith(skip):
                        invalid = True
                if invalid:
                    order += 1
                    continue
                else:
                    columns[order] = col
                    order += 1

                gradebook = GradeBook.objects.get(course=course)
                cat, created_cat = GradeCategory.objects.get_or_create(
                                                    gradebook=gradebook,
                                                    display_name=col,
                                                    defaults={'order': order,
                                                              'max_score': 1,
                                                              'weight':0.0,}
                                                    )

                item, created_item = GradeItem.objects.get_or_create(
                                                display_name=col,
                                                category__gradebook=gradebook,
                                                defaults={'order': order,
                                                          'max_score': 1,
                                                          'weight':0.0,}
                                                )
                if created_cat and created_item:
                    item.category = cat
                    item.save()

            # After processing the first row
            continue

        for idx, col in enumerate(row):
            edX_id = row[0]
            email = row[1]
            display_name = row[2]
            if Person.objects.filter(email=email, role='Learn').count():
                learner = Person.objects.filter(email=email, role='Learn')[0]
            else:
                continue

            if idx not in columns.keys():
                continue

            item_name = columns[idx]
            gitem = GradeItem.objects.get(display_name=item_name,
                                          category__gradebook=gradebook)
            prior = LearnerGrade.objects.filter(gitem=gitem, learner=learner)
            if prior.count():
                item = prior[0]
            else:
                item = LearnerGrade(gitem=gitem, learner=learner)


            if col in ('Not Attempted', 'Not Available'):
                item.not_graded_yet = True
                item.value = None
            else:
                item.not_graded_yet = False
                item.value = float(col)*100

            item.save()

    gradebook.last_update = datetime.datetime.utcnow()
    gradebook.save()


    return HttpResponse('out:' + out)





