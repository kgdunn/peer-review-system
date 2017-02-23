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
    * get the submissions sorted from lowest to highest number of COMPELTED
      reviews, and then sort from lowest to highest number of peer reviews
      ASSIGNED (not completed). So at the top of the list will be submissions
      with the least completions and assigns:

      but exclude:
        ** 1. submissions that are not complete (status='N')
        ** 2. submissions that are peer reviewed already (status='F')
        ** 3. a learner cannot evaluate their own submission
        ** 4. a learner cannot evaluate a submission from within their own group

    """
    r_template = pr.rubrictemplate  # one-to-one relationship used here

    r_actual = RubricActual.objects.filter(rubric_template__pr_process=pr)

    valid_subs_0 = Submission.objects.all().order_by('datetime_submitted').\
        order_by('number_reviews_completed')

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

def get_n_reviews(learner, pr):
    """
    How many reviews are required for this ``learner`` for this ``pr``?
    """
    if learner.role == 'Learn':
        n_reviews = pr.number_of_reviews_per_learner
    else:
        # Administrators/TAs can have unlimited number of reviews
        n_reviews = Submission.objects.filter(pr_process=pr,
                                                  is_valid=True).count()

    return n_reviews


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

            allow_submit = False
            allow_review = False
            allow_report = False
            r_actuals = []       # we want to fill this in the "review" step
            peers = {}           # we want to fill this in the "report" step

            # STEP 1: prior to submission date?
            # Code here to allow submission

            if (pr.dt_submissions_open_up.replace(tzinfo=None) <= now_time) \
                and (pr.dt_submission_deadline.replace(tzinfo=None)>now_time):
                allow_submit = True


            # STEP 2: between review start and end time?
            # Code here to display the available reviews
            # Also display the user's/group's own submission

            if (pr.dt_peer_reviews_start_by.replace(tzinfo=None) <= now_time) \
                 and (pr.dt_peer_reviews_completed_by.replace(tzinfo=None)>now_time):
                allow_review = True

                # Is this the first time the learner is here: create the
                # N = pr.number_of_reviews_per_learner rubrics for the learner
                # and return N ``RubricActual`` instances

                # If this is the second or subequent time here, simply return
                # the N ``RubricActual`` instances


                n_reviews = get_n_reviews(learner, pr)
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
            if (pr.dt_peer_reviews_received_back.replace(tzinfo=None) <= now_time):
                allow_report = True

                peers = get_peer_report_data(pr, learner)

            ctx = {'person': person_or_error,
                   'course': course,
                   'pr': pr,
                   'r_actuals': r_actuals,
                   'peers': peers,
                   'allow_submit': allow_submit,
                   'allow_review': allow_review,
                   'allow_report': allow_report,
                   }
            return render(request, 'review/welcome.html', ctx)

    else:
        return HttpResponse(("You have reached the Peer Review LTI component "
                                    "without authorization."))


def get_peer_report_data(pr, learner):
    """
    Returns a ``dict`` of the peers comments for each rubric criterion. If
    ``learner`` did not submit, then ``peers = {'n_peers': 0}``.

    peers = {
        'item-01': [3, 4, 1, 5, 7, 1],
        'item-02': [2, 1, 4, 5, 2, 6],
        'item-03': [2, 1, 4, 5, 2, 6],
        'n_peers': 6,
        'overall': 5.1,
    }
    """
    peers = {'n_peers': 0}


    # Get the scores from each of the completed_reviews
    peer_data = get_peer_grading_data(learner, pr)

    return peer_data


def get_peer_grading_data(learner, pr):
    """
    Gets the grading data and associated feedback for this ``learner`` for the
    given ``pr`` (peer review).
    """
    # Only valid submissions are accepted
    submission = Submission.objects.filter(submitted_by=learner,
                                           pr_process=pr,
                                           is_valid=True,
                                          ).order_by('-datetime_submitted')

    if submission.count() == 0:
        return {'n_peers': 0,
                'did_submit': False}

    # and only completed reviews
    completed_reviews = RubricActual.objects.filter(submission=submission[0],
                                                    status='C')

    #ActualItems and ActualOptions from the ActualRubric

    peer_data = {'did_submit': True}
    for rubric_actual in completed_reviews:
        # Process all completed reviews
        r_template = rubric_actual.rubric_template
        item_templates = r_template.ritemtemplate_set.all()


        for item in item_templates:
            # Go through each item (usually a row in the rubric matrix)
            item_scores = []
            max_score = item.max_score

            for actual_item in item.ritemactual_set.filter(submitted=True):

                for actual_option in actual_item.roptionactual_set.all():
                    score = actual_option.roption_template.score
                    item_scores.append(score)

            # OK, done with this row, for this learner, and all evalutions
            peer_data[item.order] = (max_score, item_scores)

    peer_data['n_peers'] = len(completed_reviews)
    return peer_data

def get_learner_details(ractual_code):
    """
    Verifies the learner is genuine.
    Returns: r_actual (an instance of ``RubricActual``)
             learner  (an instance of ``Person``)
    """
    logger.debug('Processing the review for r_actual={0}'.format(ractual_code))
    r_actual = RubricActual.objects.filter(unique_code=ractual_code)
    if r_actual.count() == 0:
        return HttpResponse(("You have an incorrect link. Either something "
                             "is broken in the peer review website, or you "
                             "removed/changed part of the link.")), None
    r_actual = r_actual[0]
    learner = r_actual.graded_by
    return r_actual, learner


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
    r_actual, learner = get_learner_details(ractual_code)
    if learner is None:
        # This branch only happens with error conditions.
        return r_actual
    r_item_actuals = r_actual.ritemactual_set.all()
    for item in r_item_actuals:
        item_template = item.ritem_template
        item.options = ROptionTemplate.objects.filter(rubric_item=item_template)

    ctx = {'ractual_code': ractual_code,
           'submission': r_actual.submission,
           'person': r_actual.graded_by,
           'r_actual': r_actual,
           'r_item_actuals' : r_item_actuals,
           'rubric' : r_actual.rubric_template
           }
    return render(request, 'review/review_peer.html', ctx)

@csrf_exempt
@xframe_options_exempt
def submit_peer_review_feedback(request, ractual_code):
    """
    Learner is submitting the results of their evaluation.
    """
    # 1. Check that this is POST
    # 2. Create OptionActuals
    # 3. Calculate score for evaluations?

    logger.debug("Submitted: " + str(request.POST))
    r_actual, learner = get_learner_details(ractual_code)
    r_item_actuals = r_actual.ritemactual_set.all()
    r_item_actuals
    items = {}

    # Dict: items[0] = list of the OPTIONS in the item (for that criterion)
    for item in r_item_actuals:
        item_template = item.ritem_template
        items[item_template.order] = (item,
               item_template.roptiontemplate_set.all().order_by('order'))

    # Stores the users selections as "ROptionActual" instances
    for key, value in request.POST.items():
        # Process each item in the rubric, one at a time
        if key.startswith('item-'):
            item_number = int(key.split('item-')[1])
            selected = int(value.split('option-')[1])

            # If necessary, prior submissions for the same option are adjusted
            # as being .submitted=False (perhaps the user changed their mind)
            r_opt_template = items[item_number][1][selected-1]  # "-1" is critical
            prior_options_submitted = ROptionActual.objects.filter(
                ritem_actual=items[item_number][0])
            for option in prior_options_submitted:
                option.delete()

            # Then set the "submitted" field on each OPTION
            ROptionActual.objects.get_or_create(roption_template=r_opt_template,
                                            ritem_actual=items[item_number][0],
                                            submitted=True)

            # Set the RItemActual.submitted = True for this ITEM
            items[item_number][0].submitted = True
            items[item_number][0].save()

    # And once we have processed all options and all items, we can also:
    r_actual.submitted = True
    r_actual.status = 'C' # completed
    r_actual.save()

    # And also mark the submission as having one extra submission:
    r_actual.submission.number_reviews_completed += 1
    r_actual.submission.status = 'G' # in progress
    r_actual.submission.save()

    # Reviews to still complete by this learner:
    n_graded_already = RubricActual.objects.filter(graded_by=learner,
                                                   status='C').count()
    pr = r_actual.rubric_template.pr_process
    n_to_do = max(0, get_n_reviews(learner, pr) - n_graded_already)

    return HttpResponse(('Thank you. Your review has been successfully '
                         'received. You still have to complete {0} review(s).'
                         '<br>You may close this tab/window, and return back.'
                         '').format(n_to_do,))

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
#    classlist_CSV = '/Users/kevindunn/DELETE/IO3075-classlist.csv'
    with open(classlist_CSV, 'rt') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            print(row)

            classlist[row[2] + ' ' + row[1]] = [row[2], row[3]]

    folder = '/home/kevindunn/allsub/'
    level_deep = 4
#    folder = '/Users/kevindunn/DELETE/allsub/'
#    level_deep = 5

    for root, dirs, files in os.walk(folder):
        logger.debug(root)
        if files and files[0].lower().endswith('.pdf'):

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
#            base_dir = '/Users/kevindunn/TU-Delft/CLE/peer'
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
            print(files)

