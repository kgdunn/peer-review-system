from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from django.views.decorators.clickjacking import xframe_options_exempt

# Our imports
from .models import Person, Course, PR_process, Submission
from .models import RubricActual, ROptionActual, RItemActual
from .models import RubricTemplate, ROptionTemplate, RItemTemplate
from utils import generate_random_token

# Python imports
import datetime

# Logging
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

def starting_point(request):
    """
    Bootstrap code to run on every request.

    Returns a Person instance, the course, and Peer Review (pr) instances.

    """
    person = get_create_student(request)

    course_ID = request.POST.get('context_id', None)
    course = get_object_or_404(Course, label=course_ID)

    pr_ID = request.POST.get('resource_link_title', None)
    pr = get_object_or_404(PR_process, LTI_title=pr_ID)

    if person:
        return person, course, pr
    else:
        return HttpResponse(("You are not registered in this course."))


def get_create_student(request):
    """
    Gets or creates the learner from the POST request.
    """
    if request.POST.get('ext_d2l_token_digest', None):
        first_name = request.POST['lis_person_name_given']
        email = request.POST['lis_person_contact_email_primary']
        full_name = request.POST['lis_person_name_full']
        user_ID = request.POST['user_id']
        role = request.POST['roles']
        # You can also use: request.POST['ext_d2l_role']
        if 'Instructor' in role:
            role = 'Admin'
        elif 'Student' in role:
            role = 'Learn'
    else:
        return None

    #logger.debug('About to check: name={0}, email = {1}, full_name = {2},
    #user_ID = {3}, role = {4}'.format(first_name, email, full_name, user_ID, role))
    learner, newbie = Person.objects.get_or_create(first_name=first_name,
                                                   email=email,
                                                   full_name=full_name,
                                                   role=role)

    if newbie:
        logger.info('Created new learner: %s' % learner.full_name)


    if learner:
        # Augments the learner with extra fields that might not be there
        if learner.user_ID == '':
            logger.info('Augumented user_ID on %s' % learner.email)
            learner.user_ID = user_ID
            learner.save()


    return learner

def create_items(r_actual):
    """Creates the items (rows) associated with an actual rubric"""

    r_template = r_actual.rubric_template
    r_items = RItemTemplate.objects.filter(r_template=r_template).order_by('order')

    for r_item in r_items:
        r_item_actual = RItemActual(ritem_template = r_item,
                                    r_actual = r_actual,
                                    comment = '',
                                    submitted = False,
                                    as_displayed = '')
        r_item_actual.save()



def get_next_submission_to_evaluate(pr, learner):
    """
    Gets the single next peer review submission for the approapriate peer review
    assignment (``pr``) for this ``learner``.

    Principle:
    * see if there is already a submission allocated for this learner: return
    * get the submissions with the least peer reviews ASSIGNED (not completed),
      but exclude:
        ** 1. submissions that are not complete (status='N')
        ** 2. submissions that are peer reviewed already (status='F')
        ** 3. a learner cannot evaluate their own submission
        ** 4. a learner cannot evaluate a submission from within their own group

    """
    r_template = pr.rubrictemplate  # one-to-one relationship used here

    r_actual = RubricActual.objects.filter(rubric_template__pr_process=pr)

    valid_subs_0 = Submission.objects.all().order_by('datetime_submitted')

    # Exclusion 1 and 2
    valid_subs_1_2 = valid_subs_0.exclude(status='N').exclude(status='F')

    # Exclusion 3
    valid_subs_3 = valid_subs_1_2.exclude(submitted_by=learner)

    # Exclusion 3
    # TODO
    valid_subs_4 = valid_subs_3

    # Sort from lowest to highest
    valid_subs = valid_subs_4.order_by('number_reviews_assigned')

    # Only execute the database query now, getting the one with the lowest
    # number of assigned reviews
    if valid_subs.count() == 0:
        return []
    else:
        return valid_subs[0]

@csrf_exempt
@xframe_options_exempt
def index(request):

    if request.method == 'POST':

        person_or_error, course, pr = starting_point(request)
        logger.debug('POST = ' + str(request.POST))
        logger.debug('person = ' + str(person_or_error))
        logger.debug('course = ' + str(course))
        logger.debug('pre = ' + str(pr))

        if not(isinstance(person_or_error, Person)):
            return person_or_error      # Error path if student does not exist
        else:
            learner = person_or_error
            now_time = datetime.datetime.now()

            # STEP 1: prior to submission date?
            # Code here to allow submission

            # STEP 2: between review start and end time?
            # Code here to display the available reviews
            # Also display the user's/group's own submission

            if (pr.dt_peer_reviews_start_by.replace(tzinfo=None) <= now_time) \
                 and (pr.dt_peer_reviews_completed_by.replace(tzinfo=None)>now_time):

                # Is this the first time the learner is here: create the
                # N = pr.number_of_reviews_per_learner rubrics for the learner
                # and return N ``RubricActual`` instances

                # If this is the second or subequent time here, simply return
                # the N ``RubricActual`` instances

                r_actuals = [] # this what we want to fill

                if learner.role == 'Learn':
                    n_reviews = pr.number_of_reviews_per_learner
                else:
                    # Administrators/TAs can have unlimited number of reviews
                    n_reviews = Submission.objects.filter(pr_process=pr,
                                                        is_valid=True).count()


                query = RubricActual.objects.filter(graded_by = learner,
                        rubric_template = pr.rubrictemplate).order_by('created')

                logger.debug('Need to create {0} reviews'.format(n_reviews))
                logger.debug('Found: {0}'.format(str(query)))


                if query.count() == n_reviews:
                    r_actuals = list(query)
                else:

                    # We need to create and append a few more reviews here
                    r_actuals = list(query)

                    for k in range(n_reviews - query.count()):
                        # Hit database to get the next submission to grade:
                        next_sub = get_next_submission_to_evaluate(pr, learner)
                        if next_sub:
                            next_sub.number_reviews_assigned += 1
                            next_sub.save()

                            # Create an ``rubric_actual`` instance:
                            r_actual, new_rubric = RubricActual.objects.get_or_create(\
                                        submitted = False,
                                        graded_by = learner,
                                        rubric_template = pr.rubrictemplate,
                                        submission = next_sub)

                            if new_rubric:
                                create_items(r_actual)

                            r_actuals.append(r_actual)

                            logger.debug('Created: ' + str(next_sub))

                # Now we have the peer review ojects: ``r_actual``


            # STEP 3: after the time when feedback is available?
            # Code here to display the results

            ctx = {'person': person_or_error,
                   'course': course,
                   'pr': pr,
                   'r_actuals': r_actuals,
                   }
            return render(request, 'review/welcome.html', ctx)

    else:
        return HttpResponse(("You have reached the Peer Review LTI component "
                                    "without authorization."))

@csrf_exempt
@xframe_options_exempt
def review(request, ractual_code):
    """
    From the unique URL

    1. Get the ``RubricActual`` instance
    2. Format the text for the user
    3. Handle interactions and XHR saving
    4. Capture submit signal
    5. Process the storing and saving of the objects
    """
    logger.debug('Processing the review for r_actual={0}'.format(ractual_code))
    r_actual = RubricActual.objects.filter(unique_code=ractual_code)
    if r_actual.count() == 0:
        return HttpResponse(("You have an incorrect link. Either something "
                             "is broken in the peer review website, or you "
                             "removed/changed part of the link."))
    r_actual = r_actual[0]
    learner = r_actual.graded_by

    #RItemActual.objects.filter

    #rubric = models.ForeignKey(RubricTemplate)
    #comment_required = models.BooleanField(default=False)
    #order = models.IntegerField()
    #criterion = models.TextField(help_text=('The prompt/criterion for the row '
                                            #'in the rubric'))
    #max_score = models.FloatField(help_text='Highest score achievable here')




    ctx = {'submission': r_actual.submission,
           'person': r_actual.graded_by,
           'r_actual': r_actual,
           }
    return render(request, 'review/review_peer.html', ctx)


def manual_create_uploads(request):
    """
    Manually upload the submissions for Conny Bakker IO3075 Aerobics Peer Review

    """

    import csv
    import os
    from shutil import copyfile
    from os.path import join, getsize

    pr_process = PR_process.objects.filter(id=1)[0]

    classlist = {}
    classlist_CSV = '/home/kevindunn/IO3075-classlist.csv'
    classlist_CSV = '/Users/kevindunn/DELETE/IO3075-classlist.csv'
    with open(classlist_CSV, 'rt') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            print(row)

            classlist[row[2] + ' ' + row[1]] = [row[2], row[3]]

    folder = '/home/kevindunn/allsub/'
    level_deep = 4
    folder = '/Users/kevindunn/DELETE/allsub/'
    level_deep = 5

    for root, dirs, files in os.walk(folder):
        logger.debug(root)
        if files[0].lower().endswith('.pdf'):

            # Only import PDF files

            student_folder = root.split(os.sep)[level_deep]
            student_name = student_folder.split('-')[2].strip()
            student = classlist[student_name]


            classlist[student_name].append(root + os.sep + files[0])
            learner, newbie = Person.objects.get_or_create(first_name=student[0],
                                                    email = student[1],
                                                    full_name = student_name,
                                                    role='Learn')

            learner.save()

            status = 'S'
            is_valid = True
            filename = root + os.sep + files[0]
            extension = filename.split('.')[-1]
            submitted_file_name = 'uploads/{0}/{1}'.format(pr_process.id,
                            generate_random_token(token_length=16) + '.' + extension)
            ip_address = '0.0.0.0'

            base_dir = '/var/www/peer/documents'
            base_dir = '/Users/kevindunn/TU-Delft/CLE/peer'
            copyfile(filename, base_dir + os.sep + submitted_file_name)

            sub = Submission(submitted_by = learner,
                             status = status,
                             pr_process = pr_process,
                             is_valid = True,
                             file_upload = submitted_file_name,
                             submitted_file_name = filename,
                             ip_address = ip_address,
                            )
            sub.save()


        else:
            print(files[0])





