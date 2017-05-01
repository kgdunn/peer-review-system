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
import decimal
import datetime
from collections import defaultdict, namedtuple

# Logging
import logging
logger = logging.getLogger(__name__)

def get_grade_summary(learner, gradebook):
    """
    Get the complete grade breakdown summary for a learner in a given
    ``gradebook``.

    We also return, as a second output, the grade average (total grade obtained
    so far in the course)
    """
    categories = GradeCategory.objects.filter(gradebook=gradebook)\
        .order_by('order')

    """
    How will we represent gradebook to a student? Data structure:

    [(string,decimal,{}), (string,decimal,{}), (string,decimal,{})]

    1. Outer list: holds, in order, the categories

    2. The innner tuple: holds 3 disparate elements: string, decimal, dictionary
       2a. The catogory name
       2b. The category weights (the sum of all weights should be 100%)
       2c. The dictionary* of item(s) within that category.

    3. The inner dictionaries*:
       3a. Key ('5.02', for example): indicates category 5, item 2
       3b. Value: Will be an instance of "LearnerGrade" for that item.

    * The dictionaries are sorted, just before returning and returned with:
        sorted(dict.items())  if PY3,    or    sorted(dict.iteritems()) if PY2


    To calculate the student average:
    * iterate over all the items in dictionary to calculate the score for category
    * iterate over all categories in  list, with the weight, to get overall average
    """
    grades = []
    total_grade = decimal.Decimal(0.0)
    for gcat in categories:
        items = gcat.gradeitem_set.all().order_by('order')
        if items.count() == 0:
            # No items?
            continue
        elif items.count() == 1:
            weight = max(gcat.weight, items[0].weight)
            grade = LearnerGrade.objects.filter(learner=learner, gitem=items[0])
            if grade.count() == 0:
                print('How now?')
                pass
            else:
                grades.append((gcat.display_name,
                                weight*100,
                                [('0', grade[0])]
                             ))
                if grade[0].value:
                    total_grade += weight * grade[0].value
            continue

        items_dict = {}
        item_grades = []
        item_weights = []
        category_score = decimal.Decimal(0.0)
        if gcat.spread_evenly:
            weight = decimal.Decimal(1/(items.count()+0.0))
            item_weights = [weight]*items.count()

        for idx, item in enumerate(items):
            grade = LearnerGrade.objects.filter(learner=learner, gitem=item)
            if grade.count() == 0:
                # How do we get to this point?
                item_grades.append(0.0)
                pass
            else:
                key = gcat.order + item.order/1000.0
                items_dict[key] = grade[0]
                item_weights[idx] = max(item_weights[idx], item.weight)
                if grade[0].value:
                    category_score += item_weights[idx] * grade[0].value

        # After processing all items
        total_grade += gcat.weight * category_score
        LearnerGrade_nt = namedtuple('gradeitem', ['value', 'max_score',
                                                   'not_graded_yet' ])
        items_dict[-10000] = LearnerGrade_nt(value=category_score,
                                             max_score=100,
                                             not_graded_yet=False)
        if six.PY2:
            items_dict = sorted(items_dict.iteritems())

        elif six.PY3:
            items_dict = sorted(items_dict.items())

        grades.append((gcat.display_name, gcat.weight*100, items_dict))

    return grades, total_grade

def display_grades(learner, course, pr, request):
    """
    Displays the grades to the student here.
    """
    if learner.role == 'Admin':
        ctx = {'learner': learner,
               'course': course,
               'pr': pr}

        return render(request,
                      'grades/import_grades.html', ctx)

    gradebook = GradeBook.objects.get(course=course)
    grades, total_grade = get_grade_summary(learner, gradebook)
    ctx = {'course': course,
           'gradebook': gradebook,
           'grades': grades,
           'total_grade': total_grade
           }

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
    gradebook = GradeBook.objects.get(course=course)
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

    gradebook.last_updated = datetime.datetime.utcnow()
    gradebook.save()


    return HttpResponse('out:' + out)





