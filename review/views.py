from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.template.context_processors import csrf
from django.views.decorators.clickjacking import xframe_options_exempt
from django.conf import settings
from django.template import Context, Template

# Our imports
from .models import Person, Course, PR_process
from .models import PRPhase, SelfEvaluationPhase, SubmissionPhase,\
                    PeerEvaluationPhase, FeedbackPhase
from .models import Submission
from .models import RubricActual, ROptionActual, RItemActual
from .models import RubricTemplate, ROptionTemplate, RItemTemplate
from utils import generate_random_token, send_email, get_IP_address


# Python imports
import re
import datetime
import hashlib
import numpy as np
import json
from random import shuffle

# 3rd party imports
import magic  # used to check if file uploads are of the required type

# Logging
import logging
logger = logging.getLogger(__name__)

# Move this to localsettings.py, but it is good enough here, for now.
base_dir_for_file_uploads = '/var/www/peer/documents/'


# Alternative LTI methods
# Look at https://github.com/Harvard-University-iCommons/django-auth-lti
# Brightspace: https://github.com/open-craft/django-lti-tool-provider
#---------

def starting_point(request):
    """
    Bootstrap code to run on every request.

    Returns a Person instance, the course, and Peer Review (pr) instances.

    """
    person = get_create_student(request)
    course_ID = request.POST.get('context_id', None)
    pr_ID = request.POST.get('resource_link_id', None)

    if (pr_ID is None) or (course_ID is None):
        return HttpResponse(("You are not registered in this course."))


    try:
        pr = PR_process.objects.get(LTI_id=pr_ID)
    except PR_process.DoesNotExist:
        return (HttpResponse('Config error. Try resource_link_id={}\n'.format(\
            pr_ID)), None, None)

    try:
        course = Course.objects.get(label=course_ID)
    except Course.DoesNotExist:
        return (HttpResponse('Configuration error. Try context_id={}\n'.format(\
                course_ID)), None, None)

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
        user_ID = request.POST.get('user_id', '')
        role = request.POST['roles']
        # You can also use: request.POST['ext_d2l_role']
        if 'Instructor' in role:
            role = 'Admin'
        elif 'Student' in role:
            role = 'Learn'

        learner, newbie = Person.objects.get_or_create(email=email,
                                                       role=role)


    elif request.POST.get('learner_ID', '') or (settings.DEBUG and \
                                            request.GET.get('learner_ID','')):
        logger.debug('Getting user from POST field')
        newbie = False
        learner_ID = request.POST.get('learner_ID', '') or \
                     request.GET.get('learner_ID','')

        learner = Person.objects.filter(user_ID=learner_ID)
        if learner:
            learner = learner[0]
        else:
            learner = None
    else:
        return None


    if newbie:
        learner.full_name = full_name
        learner.first_name = first_name
        learner.save()
        logger.info('Created/saved new learner: %s' % learner.full_name)

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

def get_n_reviews(learner, phase):
    """
    How many reviews are required for this ``learner`` for this ``pr``?
    """
    if learner.role == 'Learn':
        n_reviews = phase.number_of_reviews_per_learner
    else:
        # Administrators/TAs can have unlimited number of reviews
        n_reviews = Submission.objects.filter(pr_process=phase.pr,
                                              phase=phase,
                                              is_valid=True).count()

    return n_reviews

def get_peer_grading_data(learner, pr):
    """
    Gets the grading data and associated feedback for this ``learner`` for the
    given ``pr`` (peer review).
    """
    """
    IGNORE: but come back to later, to see if this is an improvement
    Returns a ``dict`` of the peers comments for each rubric criterion. If
    ``learner`` did not submit, then ``peers = {'n_reviews': 0}``.

    peers = {
        'item-01': [3, 4, 1, 5, 7, 1],
        'item-02': [2, 1, 4, 5, 2, 6],
        'item-03': [2, 1, 4, 5, 2, 6],
        'n_reviews': 6,
        'overall': 5.1,
    }
    """
    # Only valid submissions are accepted
    submission = Submission.objects.filter(submitted_by=learner,
                                           pr_process=pr,
                                           is_valid=True,
                                          ).order_by('-datetime_submitted')

    if submission.count() == 0:
        return {'n_reviews': 0,
                'did_submit': False}

    # and only completed reviews
    completed_reviews = RubricActual.objects.filter(submission=submission[0],
                                                    status='C')

    if completed_reviews.count() == 0:
        return {'n_reviews': 0,
                'did_submit': True}

    peer_data = {'did_submit': True}
    n_reviews = completed_reviews.count()
    n_items = completed_reviews[0].rubric_template.ritemtemplate_set.count()

    # Store the scores: one column per peer review, one row per item in rubric
    scores = np.zeros((n_items, n_reviews))
    comments = []
    for idx, rubric_actual in enumerate(completed_reviews):
        overall_max_score = 0.0
        r_template = rubric_actual.rubric_template

        item_scores = np.zeros(n_items) * np.NaN
        #comments = []  # <--- come back and change processing order. This only
                        # <--- works now because there is 1 text feedback field.
        ritems_submitted = rubric_actual.ritemactual_set.filter(submitted=True)
        for actual_item in ritems_submitted:
            for actual_option in actual_item.roptionactual_set.all():
                score = actual_option.roption_template.score
                item_scores[actual_item.ritem_template.order-1] = score

                if actual_option.roption_template.option_type == 'LText':
                    comments.append(actual_option.comment)


            # OK, done with this row, for this learner, and all evalutions
            peer_data[actual_item.ritem_template.order] = {
                        'max_score': actual_item.ritem_template.max_score}
            overall_max_score += actual_item.ritem_template.max_score

        # Update the scores: one column per completed review
        scores[:, idx] = item_scores

    # Process scores here:
    for idx, actual_item in enumerate(ritems_submitted):
        peer_data[actual_item.ritem_template.order]['raw'] = str(scores[idx,:])
        peer_data[actual_item.ritem_template.order]['avg_score'] = np.nanmean(scores[idx,:])

    peer_data['comments'] = comments
    peer_data['n_reviews'] = n_reviews
    peer_data['overall_max_score'] = overall_max_score
    peer_data['learner_avg'] = np.sum(np.nanmean(scores, axis=1)) # ignore NaNs
    return peer_data

def render_phase(phase, ctx_objects):
    """
    Renders the HTML template for this phase
    """
    template = Template(phase.templatetext)
    context = Context(ctx_objects)
    return template.render(context)


def get_related(self, request, learner, ctx_objects, now_time, prior):
    """
    Gets all the necessary objects used to render the template for an object
    in this phase (``self``).

    You will need to know, for certain phases, the ``request``, the ``learner``,
    the ``ctx_objects`` (context objects), the current time ``now_time``, and
    some phases (like the evaluation phase), need to know the prior phase
    (usually the submission phase).
    """
    within_phase = False
    if (self.start_dt.replace(tzinfo=None) <= now_time) \
                              and (self.end_dt.replace(tzinfo=None)>now_time):
        within_phase = True

    # Objects required for a submission: file_upload_form, (prior) submission.
    try:
        sub_phase = SubmissionPhase.objects.get(id=self.id)
        ctx_objects['self'] = sub_phase
        allow_submit = within_phase

        # Whether or not we are submitting, we might have a prior submission
        # to display
        grp_info = get_group_information(learner, self.pr.gf_process)
        submission = None
        if self.pr.uses_groups:
            # NOTE: an error condition can develop if a learner isn't
            #       allocated into a group, and you are using group submissions.
            subs = Submission.objects.filter(pr_process=self.pr,
                   group_submitted=grp_info['group_instance']).order_by(\
                       '-datetime_submitted')
        else:
            subs = Submission.objects.filter(submitted_by=learner,
                                             pr_process=self.pr).\
                  order_by('-datetime_submitted')

        if subs:
            submission = subs[0]

        ctx_objects['submission'] = submission

        if not(within_phase):
            return ctx_objects

        from . forms import UploadFF
        file_upload_form = UploadFF()

        if request.FILES:
            upload_submission(request, learner, self.pr)


        ctx_objects['allow_submit'] = allow_submit
        ctx_objects['file_upload_form'] = file_upload_form


    except SubmissionPhase.DoesNotExist:
        pass


    # Objects required for a self-review: r_actual
    try:
        selfreview_phase = SelfEvaluationPhase.objects.get(id=self.id)
        ctx_objects['self'] = selfreview_phase
        allow_self_review = within_phase
        if not(allow_self_review):
            return ctx_objects


        ctx_objects['allow_self_review'] = allow_self_review
        ctx_objects['item'] = {'unique_code': 'abc123'}  #<-- r_actual goes here

    except SelfEvaluationPhase.DoesNotExist:
        pass


    # Objects required for a peer-review: r_actuals
    try:
        peerreview_phase = PeerEvaluationPhase.objects.get(id=self.id)
        ctx_objects['self'] = peerreview_phase
        allow_review = within_phase
        if not(allow_review):
            return ctx_objects


        # Is this the first time the learner is here: create the
        # N = self.number_of_reviews_per_learner rubrics for the learner
        # and return N ``RubricActual`` instances

        # If this is the second or subequent time here, simply return
        # the N ``RubricActual`` instances

        n_reviews = get_n_reviews(learner, peerreview_phase)
        query = RubricActual.objects.filter(graded_by = learner,
                rubric_template = self.pr.rubrictemplate).order_by('created')

        logger.debug('Need to create {0} reviews'.format(n_reviews))

        if query.count() == n_reviews:
            r_actuals = list(query)
        else:

            # We need to create and append the necessary reviews here
            r_actuals = list(query)

            for k in range(n_reviews - query.count()):
                # Hit database to get the next submission to grade:
                next_sub = get_next_submission_to_evaluate(self.pr, learner)
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

        # Now we have the peer review ojects: ``r_actuals``

        ctx_objects['allow_review'] = allow_review
        ctx_objects['r_actuals'] = r_actuals

    except PeerEvaluationPhase.DoesNotExist:
        pass

    # Objects required for the feedback phase: quite a few!
    try:
        feedback_phase = FeedbackPhase.objects.get(id=self.id)
        ctx_objects['self'] = feedback_phase

        allow_report = within_phase
        if not(allow_report):
            return ctx_objects

        # This is a bit hackish, but required to work towards a deadline.
        report = get_peer_grading_data(learner, self.pr)
        report__comments = report.pop('comments', ['',])
        shuffle(report__comments)
        report__n_reviews = report.pop('n_reviews')
        report__did_submit = report.pop('did_submit')
        report__overall_max_score = report.pop('overall_max_score', 0)
        report__learner_avg = report.pop('learner_avg',0)

        report_sort = []
        for key, value in report.items():
            report_sort.append((key, value))
        report_sort = sorted(report_sort)

        ctx_objects['allow_report'] = allow_report
        ctx_objects['report__n_reviews'] = report__n_reviews
        ctx_objects['report__comments'] = report__comments
        ctx_objects['report__did_submit'] = report__did_submit
        ctx_objects['report__overall_max_score'] = report__overall_max_score
        ctx_objects['report__learner_avg'] = report__learner_avg
        ctx_objects['report'] = report_sort

    except SelfEvaluationPhase.DoesNotExist:
        pass

    return ctx_objects



@csrf_exempt
@xframe_options_exempt
def index(request):

    if request.method != 'POST':
        return HttpResponse(("You have reached the Peer Review LTI component "
                             "without authorization."))

    logger.debug('POST = ' + str(request.POST))
    person_or_error, course, pr = starting_point(request)

    if not(isinstance(person_or_error, Person)):
        return person_or_error      # Error path if student does not exist

    learner = person_or_error

    # Get all the possible phases
    phases = PRPhase.objects.filter(pr=pr, is_active=True).order_by('order')

    html = []
    now_time = datetime.datetime.utcnow()
    ctx_objects = {'now_time': now_time,
                   'person': learner,
                   'course': course,
                   'pr': pr}
    ctx_objects.update(csrf(request)) # add the csrf; used in forms

    # All the work takes place here
    prior = None
    for phase in phases:

        # Start with no ``ctx_objects``, but then add to them, with each phase.
        # A later phase can use (modify even) the state of a variable.
        # The "self" variable is certainly altered every phase
        ctx_objects['self'] = phase
        ctx_objects = get_related(phase,
                                  request,
                                  learner,
                                  ctx_objects,
                                  now_time,
                                  prior)

        # Prior element in the Peer Review chain for the next iteration
        prior = phase

        # Render the HTML for this phase: it depends on the ``pr`` settings,
        # the date and time, and related objects specifically required for
        # that phase. The rendering happens per phase. That means if the state
        # of a variable changes, it might be rendered differently in a later
        # phase [though this is not expected to be used].

        html.append(render_phase(phase, ctx_objects))
        html.append('<hr>\n')

    # end rendering
    # Return the HTTP Response

    return HttpResponse(''.join(html)   )






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


# intentional late import: for ``index``
from groups.views import get_group_information
def upload_submission(request, learner, pr_process):
    """
    Handles the upload of the user's submission.
    """

    # if within the date and time <-- that doesn't need to be checked.
    #                                 already done in the calling function

    #if the filesize is OK and    <-- not checked yet

    #if the file is of the correct type <-- we will come back to that later


    filename = request.FILES['file_upload'].name
    extension = filename.split('.')[-1]
    submitted_file_name = 'uploads/{0}/{1}'.format(pr_process.id,
                     generate_random_token(token_length=16) + '.' + extension)
    #copyfile(source_file, base_dir + os.sep + submitted_file_name)
    with open(base_dir_for_file_uploads + submitted_file_name, 'wb+') as dst:
        for chunk in request.FILES['file_upload'].chunks():
            dst.write(chunk)


    group_members = get_group_information(learner, pr_process.gf_process)

    sub = Submission(submitted_by=learner,
                     group_submitted=group_members['group_instance'],
                     status = 'S',
                     pr_process = pr_process,
                     is_valid = True,
                     file_upload = submitted_file_name,
                     submitted_file_name = filename,
                     ip_address = get_IP_address(request),
                     )
    sub.save()

    if group_members['group_name']:
        address = group_members['member_email_list']
        first_line = 'You, or someone in your group,'
        extra_line = ('That is why all members in your group will receive '
                      'this message.')
    else:
        address = [learner.email, ]
        first_line = 'You'
        extra_line = ''

    message = ('{0} have successfully submitted a document for: {1}.\n'
               'This is for the course: {2}.\n'
               '\n'
               'You may submit multiple times, up to the deadline. Only the '
               'most recent submission is kept. {3}\n'
               '\n--\n'
               'This is an automated message from the Peer Review system. '
               'Please do not reply to this email address.\n')
    message = message.format(first_line, pr_process.LTI_title,
                             pr_process.course.name,
                             extra_line)

    logger.debug('Sending email: {0}'.format(address))
    subject = 'Peer review file: successfully submitted'
    out = send_email(address, subject, message)
    logger.debug('Numer of emails sent (should be 1): {0}'.format(out[0]))

    return None

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
    r_item_actuals = r_actual.ritemactual_set.all().order_by('-modified')

    # Ensure the ``r_item_actuals`` are in the right order. These 3 lines
    # sort the ``r_item_actuals`` by using the ``order`` field on the associated
    # ``ritem_template`` instance.
    # I noticed that in some peer reviews the order was e.g. [4, 1, 3, 2]
    r_item_template_order = (i.ritem_template.order for i in r_item_actuals)
    zipped = list(zip(r_item_actuals, r_item_template_order))
    r_item_actuals, _ = list(zip(*(sorted(zipped, key=lambda x: x[1]))))

    for item in r_item_actuals:
        item_template = item.ritem_template

        hash_name = hashlib.md5(learner.full_name.encode())
        digit = re.search("\d", hash_name.hexdigest())
        if digit:
            value = int(hash_name.hexdigest()[digit.start()])
        else:
            value = 0

        # Small experiment: do rubrics from low to high (+order),  or
        # from high to low (-order), score better or worse?
        if value % 2 == 0: # even
            item.options = ROptionTemplate.objects.filter(rubric_item=item_template).order_by('-order')
        else:
            item.options = ROptionTemplate.objects.filter(rubric_item=item_template).order_by('order')

    ctx = {'ractual_code': ractual_code,
           'submission': r_actual.submission,
           'person': r_actual.graded_by,
           'r_actual': r_actual,
           'r_item_actuals' : r_item_actuals,
           'rubric' : r_actual.rubric_template,
           'person': learner,
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

    r_actual, learner = get_learner_details(ractual_code)
    r_item_actuals = r_actual.ritemactual_set.all()
    r_item_actuals
    items = {}

    # ``dict``, for example: items[3] = list of the OPTIONS in item 3
    for item in r_item_actuals:
        item_template = item.ritem_template
        items[item_template.order] = (item,
               item_template.roptiontemplate_set.all().order_by('order'))

    # Stores the users selections as "ROptionActual" instances
    for key, value in request.POST.items():
        # Process each item in the rubric, one at a time
        if key.startswith('item-'):
            item_number = int(key.split('item-')[1])

            comment = ''
            if items[item_number][1][0].option_type == 'LText':
                r_opt_template = items[item_number][1][0]
                comment = value

            if items[item_number][1][0].option_type == 'Radio':
                selected = int(value.split('option-')[1])

                # in "selected-1": the '-1' part is critical
                r_opt_template = items[item_number][1][selected-1]

            # If necessary, prior submissions for the same option are adjusted
            # as being .submitted=False (perhaps the user changed their mind)
            prior_options_submitted = ROptionActual.objects.filter(
                                             ritem_actual=items[item_number][0])

            for option in prior_options_submitted:
                option.delete()

            # Then set the "submitted" field on each OPTION
            ROptionActual.objects.get_or_create(roption_template=r_opt_template,
                                            ritem_actual=items[item_number][0],
                                            submitted=True,
                                            comment=comment)

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

    person_or_error, course, pr_process = starting_point(request)
    if not(isinstance(person_or_error, Person)):
        return person_or_error      # Error path if learner does not exist

    person = person_or_error
    if person.role == 'Learn':
        return HttpResponse(("You have reached the Group LTI component "
                             "without authorization."))

    #pr_process = PR_process.objects.filter(id=1)[0]

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

def reset_counts(request):
    """
    Resets the counts for each submission
    """

    person_or_error, course, pr_process = starting_point(request)
    if not(isinstance(person_or_error, Person)):
        return person_or_error      # Error path if learner does not exist

    person = person_or_error
    if person.role == 'Learn':
        return HttpResponse(("You have reached the Group LTI component "
                             "without authorization."))

    #pr_process = PR_process.objects.filter(id=1)[0]

    all_subs = Submission.objects.filter(pr_process=pr_process)
    for idx, sub in enumerate(all_subs):
        sub.number_reviews_completed = 0
        sub.number_reviews_assigned = 0
        sub.save()
        logger.debug('Counts reset for: {0}'.format(sub))

    return HttpResponse('All counts reset on {0} submissions.'.format(idx+1))

@csrf_exempt
def get_stats_comments(request):
    """
    Gets all the student grades and comments
    """
    person_or_error, course, pr_process = starting_point(request)
    if not(isinstance(person_or_error, Person)):
        return person_or_error      # Error path if learner does not exist

    person = person_or_error
    if person.role == 'Learn':
        return HttpResponse(("You have reached the Group LTI component "
                             "without authorization."))

    all_subs = Submission.objects.filter(pr_process=pr_process)

    with open('results.tsv', 'wt') as statsfile:
        statsfile.write('FullName\tEmail\tQuestion1Score\tQuestion2Score\tQuestion3Score\t Question4Score\tAverageOutOf12\tComments\n')
        for idx, sub in enumerate(all_subs):

            peer = get_peer_grading_data(sub.submitted_by, pr_process)
            statsfile.write('{}\t{}\t{:4.2f}\t{:4.2f}\t{:4.2f}\t{:4.2f}\t{:4.2f}\t{}\n'.format(
                sub.submitted_by.full_name,
                sub.submitted_by.email,
                peer[1]['avg_score'],
                peer[2]['avg_score'],
                peer[3]['avg_score'],
                peer[4]['avg_score'],
                peer['learner_avg'],
                str(peer['comments']).encode('utf-8')))


    return HttpResponse('All counts reset on {0} submissions.'.format(idx+1))
