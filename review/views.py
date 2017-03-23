from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.template.context_processors import csrf
from django.views.decorators.clickjacking import xframe_options_exempt
from django.conf import settings
from django.template import Context, Template, loader
from django.utils import timezone

# Our imports
from .models import Person, Course, PR_process
from .models import PRPhase, SelfEvaluationPhase, SubmissionPhase,\
                    PeerEvaluationPhase, FeedbackPhase, GradeReportPhase,\
                    ViewAllSubmissionsPhase
from .models import Submission, ReviewReport, GradeComponent
from .models import RubricActual, ROptionActual, RItemActual
from .models import RubricTemplate, ROptionTemplate, RItemTemplate
from stats.views import create_hit
from utils import generate_random_token, send_email, get_IP_address


# Python imports
import re
import os
import datetime
import hashlib
import numpy as np
import json
from random import shuffle
from collections import defaultdict

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
    course_ID = request.POST.get('context_id', None) or (settings.DEBUG and \
                             request.GET.get('context_id', None))

    pr_ID = request.POST.get('resource_link_id', None) or (settings.DEBUG and \
                             request.GET.get('resource_link_id', None))


    if (pr_ID is None) or (course_ID is None):
        return (HttpResponse(("You are not registered in this course. NCNPR")),
                None, None)

    try:
        pr = PR_process.objects.get(LTI_id=pr_ID)
    except PR_process.DoesNotExist:
        return (HttpResponse('Config error. Try resource_link_id={}\n'.format(\
            pr_ID)), None, None)

    try:
        if ' ' in course_ID:
            course_ID = course_ID.replace(' ', '+') # For edX course ID's

        course = Course.objects.get(label=course_ID)
    except Course.DoesNotExist:
        return (HttpResponse('Configuration error. Try context_id={}\n'.format(\
                course_ID)), None, None)

    person = get_create_student(request, course, pr)
    if person:
        return person, course, pr
    else:
        return (HttpResponse(("You are not registered in this course.")), None,
                None)


def recognise_LTI_LMS(request):
    """
    Trys to recognize the LMS from the LTI post.

    Returns one of ('edx', 'brightspace', 'coursera', None). The last option
    is if nothing can be determined.
    """
    if settings.DEBUG:
        request.POST = request.GET # only on the development server

    if request.POST.get('learner_ID', ''):
        return None   # Used for form submissions internally.
    if request.POST.get('resource_link_id', '').find('edx.org')>0:
        return 'edx'
    elif request.POST.get('ext_d2l_token_digest', None):
        return 'brightspace'
    elif request.POST.get('tool_consumer_instance_guid', '').find('coursera')>1:
        return 'coursera'
    else:
        return None


def get_create_student(request, course, pr):
    """
    Gets or creates the learner from the POST request.
    Also send the ``course``, for the case where the same user email is enrolled
    in two different systems (e.g. Brightspace and edX).
    """
    newbie = False
    LTI_consumer = recognise_LTI_LMS(request)
    if LTI_consumer in ('brightspace', 'edx', 'coursera'):
        email = request.POST.get('lis_person_contact_email_primary', '')
        display_name = request.POST.get('lis_person_name_full', '')
        if LTI_consumer == 'edx':
            display_name = display_name or \
                                 request.POST.get('lis_person_sourcedid', '')
        user_ID = request.POST.get('user_id', '')
        role = request.POST.get('roles', '')
        # You can also use: request.POST['ext_d2l_role'] in Brightspace
        if 'Instructor' in role:
            role = 'Admin'
        elif 'Student' in role:
            role = 'Learn'
        learner, newbie = Person.objects.get_or_create(email=email,
                                                       user_ID=user_ID,
                                                       role=role)

    elif request.POST.get('learner_ID', '') or (settings.DEBUG and \
                                            request.GET.get('learner_ID','')):

        # Used to get the user when they are redirected outside the LMS.
        # and most often, if a form is being filled in, and returned via POST.
        logger.debug('Getting user from POST field')

        learner_ID = request.POST.get('learner_ID', '') or \
                     request.GET.get('learner_ID','')

        learner = Person.objects.filter(user_ID=learner_ID)
        if learner.count() == 1:
            return learner[0]
        elif learner.count() > 1:
            # Find the learner in this course
            # TODO still. This is the case where the same email address is used
            #             in more than 1 platform (e.g. Brightspace and edX)
            return learner[0]
        else:
            learner = None
    else:
        return None

    if newbie:
        learner.display_name = display_name
        learner.save()
        logger.info('Created/saved new learner: %s' % learner.display_name)

    if learner:
        # Augments the learner with extra fields that might not be there
        if learner.user_ID == '':
            logger.info('Augumented user_ID on %s' % learner.email)
            learner.user_ID = user_ID
            learner.save()


    return learner


def get_create_actual_rubric(learner, template, submission):
    """
    Creates a new actual rubric for a given ``learner`` (the person doing the)
    evaluation. It will be based on the parent template defined in ``template``,
    and for the given ``submission`` (either their own submission if it is a
    self-review, or another person's submission for peer-review).

    If the rubric already exists it returns it.
    """
    # Create an ``rubric_actual`` instance:
    r_actual, new_rubric = RubricActual.objects.get_or_create(\
                        graded_by = learner,
                        rubric_template = template,
                        submission = submission,
                        defaults={'started': timezone.now(),
                                  'completed': timezone.now(),
                                  'status': 'A',         # To be explicit
                                  'submitted': False,
                                  'score': 0.0,
                                  'word_count': 0})


    if new_rubric:

        # Creates the items (rows) associated with an actual rubric
        for r_item in RItemTemplate.objects.filter(r_template=template)\
                                                           .order_by('order'):
            r_item_actual = RItemActual(ritem_template = r_item,
                                        r_actual = r_actual,
                                        comment = '',
                                        submitted = False)
            r_item_actual.save()

    return r_actual, new_rubric


def get_submission(learner, phase=None, pr_process=None, search_earlier=False):
    """
    Gets the ``submission`` instance at the particular ``phase`` in the PR
    process.
    Allow some flexibility in the function signature here, to allow retrieval
    via the ``pr_process`` in the future.
    """
    # Whether or not we are submitting, we might have a prior submission
    # to display
    grp_info = {}
    if phase:
        grp_info = get_group_information(learner, phase.pr.gf_process)


    submission = None
    subs = Submission.objects.filter(is_valid=True, pr_process=phase.pr)
    if phase.pr.uses_groups:
        # NOTE: an error condition can develop if a learner isn't
        #       allocated into a group, and you are using group submissions.

        if search_earlier:

            # NOTE: will only get submissions for a phase LTE (less than and
            #       equal) to the current ``phase``.

            subs = subs.filter(phase__order__lte=phase.order,
                               group_submitted=grp_info['group_instance'])\
                                                .order_by('-datetime_submitted')
        else:
            # This will only get it in the exact phase required
            subs = subs.filter(phase__order=phase.order,
                               group_submitted=grp_info['group_instance'])\
                                                            .order_by('-datetime_submitted')
    else:
        # Individual submission
        subs = subs.filter(submitted_by=learner).order_by('-datetime_submitted')

    if subs:
        return subs[0]
    else:
        return None


def get_next_submission_to_evaluate(phase, learner, return_all=False):
    """
    Gets the single next peer review submission for the approapriate peer review
    assignment phase (``phase``) for this ``learner``. Will ``return_all`` valid
    submissions, if so requested.

    Principle:


    * get the submissions sorted from lowest to highest number of COMPELTED
      reviews, and then sort from lowest to highest number of peer reviews
      ASSIGNED (not completed). So at the top of the list will be submissions
      with the least completions and assigns:

      but exclude:
        ** 0. invalid submissions (e.g. duplicates)
        ** 1. find only submissions of the phase immediately prior to this one
              (going only as far back in the order history as needed)
        ** 2. submissions that are not complete (status='N')
        ** 3. submissions that are peer reviewed already (status='F')
        ** 4. a learner cannot evaluate their own submission
        ** 5. a learner cannot evaluate a submission from within their own group

    """
    this_order_step = phase.order
    prior_step = max(0, this_order_step-1)

    # Exclusions 0 and 1:
    while (prior_step>=0):
        valid_subs_0_1 = Submission.objects.filter(is_valid=True,
                                                   pr_process=phase.pr,
                                                   phase__order=prior_step).\
                        order_by('datetime_submitted').\
                        order_by('number_reviews_completed')

        if valid_subs_0_1.count() == 0:
            prior_step = max(-1, prior_step-1)
        else:
            break

    # Exclusion 2 and 3
    valid_subs_2_3 = valid_subs_0_1.exclude(status='N').exclude(status='F')

    # Exclusion 4: own submission
    valid_subs_4 = valid_subs_2_3.exclude(submitted_by=learner)

    # Exclusion 5: groups
    if phase.pr.uses_groups:
        grp_info = get_group_information(learner, phase.pr.gf_process)
        valid_subs_5 = valid_subs_4.exclude(group_submitted=\
                                                     grp_info['group_instance'])
    else:
        valid_subs_5 = valid_subs_4

    # Sort all of these now, from lowest to highest
    valid_subs = valid_subs_5.order_by('number_reviews_assigned')

    # Execute the database query only now, getting the one with the submission
    # with the lowest number of assigned reviews
    if valid_subs.count() == 0:
        return []
    elif return_all:
        return valid_subs
    else:
        return valid_subs[0]


def get_peer_grading_data(learner, phase, role_filter=''):
    """
    Gets the grading data and associated feedback for this ``learner`` for the
    given ``phase`` in the peer review.

    Filters for the role of the grader, can also be provided.
    """
    submission = get_submission(learner, phase, search_earlier=True)
    peer_data = dict()
    peer_data['n_reviews'] = 0
    peer_data['overall_max_score'] = 0.0
    peer_data['learner_total'] = 0.0
    peer_data['did_submit'] = False

    if submission is None:
        return peer_data

    # and only completed reviews
    if role_filter:
        reviews = RubricActual.objects.filter(submission=submission,
                                              status='C',
                                              graded_by__role=role_filter)
    else:
        reviews = RubricActual.objects.filter(submission=submission, status='C')

    if reviews.count() == 0:
        # You must return here if there are no reviews. The rest of the
        # code is not otherwise valid.
        peer_data['did_submit'] = True
        return peer_data

    peer_data['did_submit'] = True
    peer_data['n_reviews'] = n_reviews = reviews.count() # completed! reviews

    n_items = reviews[0].rubric_template.ritemtemplate_set.count()

    # Iterate per completed review, then per item, and within each item
    # we will iterate per option (extracting the score or comment)


    raw_scores = np.zeros((n_items, n_reviews)) * np.nan
    for idxr, completed_review in enumerate(reviews):
        # The ``order_by`` is important for consistency
        items = completed_review.ritemactual_set.filter(submitted=True)\
                                                            .order_by('id')
        overall_max_score = 0.0 # just compute this on the last completed_review
        for idxi, item in enumerate(items):

            ritem_template = item.ritem_template

            # Each key/value in the dictionary stores a list. The list has 5
            # elements:
            #   1. [list of raw scores] {or comments from peers}
            #   2. the maximum for this item,
            #   3. the average for this learner for this item
            #   4. the class average (not used at the moment)
            #   5. the comments from the instructor or TA (if any)
            if ritem_template not in peer_data:
                peer_data[ritem_template] = [[], 0.0, 0.0, idxi, []]


            for option in item.roptionactual_set.filter(submitted=True):

                if ritem_template.option_type == 'LText':
                    if completed_review.graded_by.role == 'Learn':
                        peer_data[ritem_template][0].append(option.comment)
                    else:
                        peer_data[ritem_template][4].append(option.comment)
                else:
                    score = option.roption_template.score
                    raw_scores[idxi, idxr] = score
                    peer_data[ritem_template][0].append(score)

            # OK, done with this row, for this learner, and all evalutions
            peer_data[ritem_template][1] = item.ritem_template.max_score
            overall_max_score += item.ritem_template.max_score

        # All done processing a review


    # All the reviews for this submission have been processed.
    # Process scores here to calculate the average. Just use the last
    # completed review to iterate over, no
    items = completed_review.ritemactual_set.filter(submitted=True).order_by('id')
    for idxi, item in enumerate(items):
        ritem_template = item.ritem_template
        peer_data[ritem_template][2] = np.nanmean(raw_scores[idxi,:])

    peer_data['overall_max_score'] = overall_max_score
    # ignore NaNs: these will show up for items, such as comments
    peer_data['learner_total'] = np.nansum(np.nanmean(raw_scores, axis=1))
    try:
        average = peer_data['learner_total'] / \
                                           peer_data['overall_max_score'] * 100
    except ZeroDivisionError:
        average = 0.0
    peer_data['learner_average'] = ('{:0.1f} out of a maximum of {:0.0f} '
                                    'points; {:3.1f}%').format(
                    peer_data['learner_total'], peer_data['overall_max_score'],
                    average)
    return peer_data

def render_phase(phase, ctx_objects):
    """
    Renders the HTML template for this phase
    """
    if phase.show_dates:
        template = Template(\
        """
        <div class="end_dt"><b>Ends</b>: {{self.end_dt|date:"D, d F"}} at
                                         {{self.end_dt|time:"H:i" }}</div>
        <div class="start_dt"><em>Starts</em>:
                                {{self.start_dt|date:"D, d F"}} at
                                {{self.start_dt|time:"H:i" }}&nbsp;&nbsp;</div>
        """ + phase.templatetext)
    else:
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

        # Remove the prior submission from the dict, so that PRs that use
        # multiple submission steps get the correct phase's submission
        ctx_objects.pop('submission', None)
        ctx_objects['submission'] = get_submission(learner, self)

        if not(within_phase):
            return ctx_objects

        from . forms import UploadFF
        file_upload_form = UploadFF()

        if request.FILES:
            submission = upload_submission(request, learner, self.pr, sub_phase)
            ctx_objects['submission'] = submission

        sub_phase.submission = ctx_objects['submission']
        sub_phase.allow_submit = ctx_objects['allow_submit'] = allow_submit
        sub_phase.file_upload_form = ctx_objects['file_upload_form'] = file_upload_form


    except SubmissionPhase.DoesNotExist:
        pass


    # Objects required for a self-review: r_actual
    try:
        selfreview_phase = SelfEvaluationPhase.objects.get(id=self.id)
        ctx_objects['self'] = selfreview_phase
        allow_self_review = within_phase


        # Get the submission from the prior step. Note, this must be a
        # relevant submission (i.e. group or individual submission) related
        # to a prior Submission step. I'm not going to check it here, but the
        # variable ctx_objects['submission'] should be the correct one
        #
        # Submission.objects.filter(phase=prior, learner=..., group=...)
        ctx_objects['submission']

        r_template = RubricTemplate.objects.get(pr_process=self.pr,
                                                phase=self)

        # Get/create the R_actual for the self-review, only if there
        # is an actual submission.
        if ctx_objects['submission'] and within_phase:
            r_actual, _ = get_create_actual_rubric(learner,
                                                   r_template,
                                                   ctx_objects['submission'])
        else:
            r_actual = None

        ctx_objects['allow_self_review'] = allow_self_review
        ctx_objects['own_submission'] = r_actual

        # For this phase, we do require to return "late"; the ``own_submission``
        # is required for the phase following this: the own-submission review.

        if not(allow_self_review):
            return ctx_objects

    except SelfEvaluationPhase.DoesNotExist:
        pass


    # Objects required for a peer-review: r_actuals
    try:
        peerreview_phase = PeerEvaluationPhase.objects.get(id=self.id)
        ctx_objects['self'] = peerreview_phase
        allow_review = within_phase
        ctx_objects['allow_review'] = allow_review

        if not(allow_review) and learner.role == 'Learn':
            return ctx_objects

        # Administrator roles can go further, even if we are not within the
        # time range for peer-review. This is so admins can view, and even
        # evaluate all students submissions.


        # Is this the first time the learner is here: create the
        # N = self.number_of_reviews_per_learner rubrics for the learner
        # and return N ``RubricActual`` instances

        # If this is the second or subequent time here, simply return
        # the N ``RubricActual`` instances

        # Which was the submission phase, prior to this one. A good starting
        # guess is ``prior``, and then we work backwards. If none is found,
        # then return the ``0``.
        phase = prior
        while (phase.order >= 0):
            try:
                phase = SubmissionPhase.objects.get(is_active=True,
                                                    pr=self.pr,
                                                    order=phase.order)

                break
            except SubmissionPhase.DoesNotExist:
                phase = PRPhase.objects.get(is_active=True, pr=self.pr,
                                order=phase.order-1)


        max_reviews = Submission.objects.filter(pr_process=phase.pr,
                                                phase=phase,
                                                is_valid=True).count()

        if learner.role == 'Learn':
            n_reviews = peerreview_phase.number_of_reviews_per_learner
        else:
            # Administrators/TAs can have unlimited number of reviews
            n_reviews = max_reviews


        # Which template are we using in this phase?
        r_template = RubricTemplate.objects.get(phase=self)
        query = RubricActual.objects.filter(graded_by=learner,
                        rubric_template=r_template).order_by('created')

        # We need to create and append the necessary reviews here
        r_actuals = list(query)

        logger.debug('Found {0} reviews; required: {1}'.format(len(r_actuals),
                                                               n_reviews))
        n_iter = 0
        next_subs = get_next_submission_to_evaluate(self, learner,
                                                    return_all=True)
        while (len(r_actuals) != n_reviews) and (n_iter < len(next_subs)):


            # Hit database to get the next submission to grade:
            next_sub = next_subs[n_iter]
            n_iter += 1
            if next_sub:
                r_actual, new = get_create_actual_rubric(learner=learner,
                                                    template=r_template,
                                                    submission=next_sub)

                if new:
                    next_sub.number_reviews_assigned += 1
                    next_sub.save()
                    r_actuals.append(r_actual)
                    logger.debug('Created r_actual: ' + str(r_actual))

        if learner.role != 'Learn':
            sub_stats = {}  # r_actual_stats
            all_ra = RubricActual.objects.filter(rubric_template=r_template)

            # admin_grader_completed: bool (0 or 1 int)
            # admin_grader_inprogress: bool
            # learner_grader_completed: int
            # learner_grader_inprogress: int

            for item in all_ra:
                key = item.submission
                if sub_stats.get(key, None) is None:
                    sub_stats[key] = defaultdict(int)
                if item.graded_by.role == 'Admin':
                    if not(sub_stats[key]['admin_grader_inprogress']):
                        if item.status == 'P':
                            sub_stats[key]['admin_grader_inprogress'] = 1
                    if not(sub_stats[key]['admin_grader_completed']):
                        if item.status == 'C':
                            sub_stats[key]['admin_grader_completed'] = 1

                if item.graded_by.role == 'Learn':
                    if item.status in ('P', 'A'):
                        sub_stats[key]['learner_grader_inprogress'] += 1
                    if item.status == 'C':
                        sub_stats[key]['learner_grader_completed'] += 1


            # Now that we have statistics for each submission, associate it
            # back to the r_actuals for the admins:

            for item in r_actuals:
                key = item.submission
                item.summary_stats = sub_stats[key]

        # Now we have the peer review ojects: ``r_actuals``
        ctx_objects['r_actuals'] = r_actuals

        content = loader.render_to_string('review/admin-peer-review-status.html',
                                          context=ctx_objects,
                                          request=request,
                                          using=None)

        ctx_objects['admin_overview'] = content


    except PeerEvaluationPhase.DoesNotExist:
        pass


    # Objects required for the feedback phase:
    try:
        feedback_phase = FeedbackPhase.objects.get(id=self.id)
        ctx_objects['self'] = feedback_phase

        allow_report = within_phase
        ctx_objects['allow_report'] = allow_report
        if not(allow_report):
            return ctx_objects

        group = get_group_information(learner, ctx_objects['pr'].gf_process)
        if not(ctx_objects['submission']):
            report = None

        if learner.role == 'Learn':
            report, _ = ReviewReport.objects.get_or_create(learner = learner,
                                           group = group['group_instance'],
                                           phase = feedback_phase,
                                           submission=ctx_objects['submission'])

        ctx_objects['report'] = report

    except FeedbackPhase.DoesNotExist:
        pass


    # Objects required for a grade report: grade_report_table
    try:
        gradereport_phase = GradeReportPhase.objects.get(id=self.id)
        ctx_objects['self'] = gradereport_phase
        allow_grades = within_phase

        if not(allow_grades) and learner.role == 'Learn':
            return ctx_objects

        ctx_objects['allow_grades'] = allow_grades
        grade_components = GradeComponent.objects.filter(pr=ctx_objects['pr']).\
            order_by('order')
        total_grade = 0.0
        ctx_local = {}
        for item in grade_components:
            grade_achieved, grade_detail = get_grading_percentage(item, learner)
            total_grade += item.weight * grade_achieved
            item.grade_achieved = grade_achieved
            item.component_weight = item.weight * grade_achieved
            item.grade_detail = grade_detail
            item.max_weight = item.weight * 100.0

        ctx_local['grade_components'] = grade_components
        ctx_local['overall_grade'] = total_grade
        content = loader.render_to_string('review/peer-review-grades.html',
                                          context=ctx_local,
                                          request=request,
                                          using=None)
        ctx_objects['self'].grade_report_table = content

    except GradeReportPhase.DoesNotExist:
        pass


    try:
        viewall_phase = ViewAllSubmissionsPhase.objects.get(id=self.id)
        ctx_objects['self'] = viewall_phase
        uploaded_items_exist = within_phase
        ctx_objects['uploaded_items_exist'] = uploaded_items_exist
        if not(uploaded_items_exist):
            return ctx_objects

        phase = prior
        while (phase.order >= 0):
            try:
                phase = SubmissionPhase.objects.get(is_active=True,
                                                    pr=self.pr,
                                                    order=phase.order)

                break
            except SubmissionPhase.DoesNotExist:
                phase = PRPhase.objects.get(is_active=True, pr=self.pr,
                                order=phase.order-1)


        uploaded_items = Submission.objects.filter(phase=phase,
                                                 is_valid=True,
                                                 )
        if uploaded_items.count() == 0:
            uploaded_items_exist = False
        else:
            uploaded_items_exist = True # for certainty
        ctx_objects['uploaded_items'] = uploaded_items
        ctx_objects['uploaded_items_exist'] = uploaded_items_exist

    except ViewAllSubmissionsPhase.DoesNotExist:
        pass

    # This is the last step, no matter what
    return ctx_objects


@csrf_exempt
@xframe_options_exempt
def index(request):

    if request.method != 'POST' and (len(request.GET.keys())==0):
        return HttpResponse("You have reached the Peer Review LTI component.")

    person_or_error, course, pr = starting_point(request)

    if not(isinstance(person_or_error, Person)):
        return person_or_error      # Error path if student does not exist

    learner = person_or_error
    logger.debug('Learner entering: {0}'.format(learner))


    create_hit(request, item=learner, event='login', user=learner,)

    # Get all the possible phases
    phases = PRPhase.objects.filter(pr=pr, is_active=True).order_by('order')

    html = []
    now_time = datetime.datetime.utcnow()
    ctx_objects = {'now_time': now_time,
                   'person': learner,
                   'course': course,
                   'pr': pr}
    ctx_objects.update(csrf(request)) # add the csrf; used in forms

    global_page = """{% extends "review/base.html" %}{% block content %}<hr>
    <!--SPLIT HERE-->\n{% endblock %}"""
    template_page = Template(global_page)
    context = Context(ctx_objects)
    page_header_footer = template_page.render(context)
    page_header, page_footer = page_header_footer.split('<!--SPLIT HERE-->')
    html.append(page_header)


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


        # Render the HTML for this phase: it depends on the ``pr`` settings,
        # the date and time, and related objects specifically required for
        # that phase. The rendering happens per phase. That means if the state
        # of a variable changes, it might be rendered differently in a later
        # phase [though this is not expected to be used].

        html.append(render_phase(phase, ctx_objects))
        html.append('<hr>\n')

        # Prepare for the next iteration in this loop.
        # Prior element in the Peer Review chain for the next iteration.
        # Note: the prior is NOT of type "PRPhase", it is the actual
        #       prior phase instance.
        prior = ctx_objects['self']

    # end rendering
    html.append(page_footer)

    # Return the HTTP Response
    return HttpResponse(''.join(html))


def get_learner_details(ractual_code):
    """
    Verifies the learner is genuine.
    Returns: r_actual (an instance of ``RubricActual``)
             learner  (an instance of ``Person``)
    """
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
def upload_submission(request, learner, pr_process, phase):
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

    base_full_path = base_dir_for_file_uploads + 'uploads/{0}/'.format(pr_process.id)
    try:
        os.makedirs(base_full_path)
    except OSError:
        if not os.path.isdir(base_full_path):
            logger.error('Cannot create directory for upload: {0}'.format(
                                        base_full_path))
            raise

    with open(base_dir_for_file_uploads + submitted_file_name, 'wb+') as dst:
        for chunk in request.FILES['file_upload'].chunks():
            dst.write(chunk)


    group_members = get_group_information(learner, pr_process.gf_process)

    prior = Submission.objects.filter(status='S',
                                      pr_process=pr_process,
                                      phase=phase,
                                      is_valid=True)
    if prior:
        for item in prior:
            logger.debug('Set old submission False: {0} and name "{1}"'.format(\
                        str(item), item.submitted_file_name))
            item.is_valid = False
            item.save()

    sub = Submission(submitted_by=learner,
                     group_submitted=group_members['group_instance'],
                     status='S',
                     pr_process=pr_process,
                     phase=phase,
                     is_valid=True,
                     file_upload=submitted_file_name,
                     submitted_file_name=filename,
                     ip_address=get_IP_address(request),
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
    subject = phase.name + ' for peer review: successfully submitted'
    out = send_email(address, subject, message)
    logger.debug('Number of emails sent (should be 1): {0}'.format(out[0]))

    return sub


#@csrf_exempt
@xframe_options_exempt
def xhr_store_text(request, ractual_code):
    """
    Processes the XHR for text fields: it is slightly different than the
    ``xhr_store`` function elsewhere in this file.
    """
    for item, comment in request.POST.items():
        if not comment:
            continue
        comment = comment.encode('utf-8').strip()
        if not item.startswith('item-'):
            continue
        else:
            item_number = int(item.split('item-')[1])


        r_actual, learner = get_learner_details(ractual_code)
        if learner is None:
            return HttpResponse('')
        r_item_actual = r_actual.ritemactual_set.filter(\
                                            ritem_template__order=item_number)

        if r_item_actual.count() == 0:
            continue
        else:
            r_item = r_item_actual[0]

        item_template = r_item.ritem_template
        r_options = item_template.roptiontemplate_set.all().order_by('order')

        r_opt_template = None
        if item_template.option_type == 'LText':
            r_opt_template = r_options[0]
        else:
            continue

        # If necessary, prior submissions for the same option are adjusted
        # as being .submitted=False (perhaps the user changed their mind)
        prior_options_submitted = ROptionActual.objects.filter(ritem_actual\
                                                                       =r_item)
        if prior_options_submitted.count():
            r_option_actual = prior_options_submitted[0]
            if r_option_actual.comment != comment:
                r_option_actual.comment = comment
                r_option_actual.submitted = True
                logger.debug('XHR: [{0}]: item={1}; comment='.format(learner,
                                    item_number,
                                    comment.replace(b'\n', b'||')[0:50]))
                r_option_actual.save()
        else:

            # Then set the "submitted" field on each OPTION
            ROptionActual.objects.get_or_create(roption_template=r_opt_template,
                            # This is the way we bind it back to the user!
                            ritem_actual=r_item,
                            submitted=True,
                            comment=comment)
            logger.debug('XHR: [{0}]: item={1}; comment={2}'.format(learner,
                                        item_number,
                                        comment.replace(b'\n', b'||')[0:50]))

        # Set the RItemActual.submitted = True for this ITEM
        r_item.submitted = True
        r_item.save()

        if r_actual.status == 'A':
            r_actual.status = 'P'
            r_actual.started = timezone.now()
            r_actual.save()

    # Return with something at the end
    now_time = datetime.datetime.now()
    return HttpResponse('Your change was saved [{}]'.format(
                        now_time.strftime('%H:%M:%S')))


#@csrf_exempt
@xframe_options_exempt
def xhr_store(request, ractual_code):
    """
    Stores, in real-time, the results from the peer review.
    """
    option = request.POST.get('option', None)
    if option is None or option=='option-NA':
        return HttpResponse('')

    item_post = request.POST.get('item', None)
    if item_post.startswith('item-'):
        item_number = int(item_post.split('item-')[1])
    else:
        return HttpResponse('')


    r_actual, learner = get_learner_details(ractual_code)
    if learner is None:
        # This branch only happens with error conditions.
        return HttpResponse('')
    r_item_actual = r_actual.ritemactual_set.filter(\
                                             ritem_template__order=item_number)
    if r_item_actual.count() == 0:
        return HttpResponse('')
    else:
        r_item = r_item_actual[0]


    item_template = r_item.ritem_template
    r_options = item_template.roptiontemplate_set.all().order_by('order')

    r_opt_template = None
    comment = ''
    if item_template.option_type == 'LText':
        if value:
            r_opt_template = r_options[0]
            comment = value
        else:
            return HttpResponse('')

    if (item_template.option_type == 'Radio') or \
       (item_template.option_type == 'DropD'):
        selected = int(option.split('option-')[1])

        # in "selected-1": the '-1' part is critical
        try:
            r_opt_template = r_options[selected-1]
        except (IndexError, AssertionError):
            return HttpResponse('Invalid')

    # If necessary, prior submissions for the same option are adjusted
    # as being .submitted=False (perhaps the user changed their mind)
    prior_options_submitted = ROptionActual.objects.filter(ritem_actual=r_item)
    prior_options_submitted.update(submitted=False)

    # Then set the "submitted" field on each OPTION
    ROptionActual.objects.get_or_create(roption_template=r_opt_template,

                        # This is the way we bind it back to the user!
                        ritem_actual=r_item,
                        submitted=True,
                        comment=comment)

    # Set the RItemActual.submitted = True for this ITEM
    r_item.submitted = True
    r_item.save()

    if r_actual.status == 'A':
        r_actual.status = 'P'
        r_actual.started = timezone.now()
        r_actual.save()


    logger.debug('XHR: [{0}]: item={1}; option={2}'.format(learner,
                                                           item_number,
                                                           option))

    now_time = datetime.datetime.now()
    return HttpResponse('Your change was saved [{}]'.format(
                    now_time.strftime('%H:%M:%S')))


@csrf_exempt
@xframe_options_exempt
def review(request, ractual_code):
    """
    From the unique URL:

    1. Get the ``RubricActual`` instance
    2. Format the text for the user
    3. Handle interactions and XHR saving.


    The user coming here is either:
    a) reviewing their own report (self-review)
    b) reviewing a peer's report (peer-review)
    c) self-review, but with their group's feedback (read-only mode)
    d) peer-review, but with their peer's feedback (peer-review, read-only)
    """
    self_review = True
    r_actual, learner = get_learner_details(ractual_code)
    if learner is None:

        # Maybe this is peer-review feedback coming along?
        review_report = ReviewReport.objects.filter(unique_code=ractual_code)
        if review_report.count() == 0:
            # This branch only happens with error conditions.
            return HttpResponse(("You have an incorrect link. Either something "
                                 "is broken in the peer review website, or you "
                                 "removed/changed part of the link."))


        review_report = review_report[0]
        learner = review_report.learner
        phase = review_report.phase
        pr = phase.pr
        if isinstance(r_actual, HttpResponse):
            self_review = False
            # In other words, this is a read-only review of the peer-feedback
            r_actual = RubricActual.objects.filter(status='C',
                                        submission=review_report.submission, )

            # Just use one of the peer's rubric to construct the report
            if r_actual.count() > 0:
                r_actual = r_actual[0]
            else:
                # Shouldn't be able to reach this point. But it catches a bad
                # template in the PRPhase for feedback.
                return HttpResponse('No review available. Admin?')

    else:
        pr = r_actual.rubric_template.pr_process
        phase = r_actual.rubric_template.phase

        start_dt = r_actual.rubric_template.phase.start_dt
        end_dt = r_actual.rubric_template.phase.end_dt
        now_time = datetime.datetime.utcnow()
        if end_dt.replace(tzinfo=None) < now_time:
            logger.debug("Outdated ractual used: {0} by {1}".format(\
                                            ractual_code, learner))
            return HttpResponse(("You have used an outdated link. That review "
                                 "cannot be completed at this time; if you "
                                 "believe this to be an error, please contact "
                                 "your course coordinator or TA."))



    # Should we show feedback, or not, within the rubric?
    # ``r_actual.rubric_template.phase`` is current phase for the
    # ``r_actual``. Get the ``order`` number for the phase. Search
    # *forward*, and if that phase allows showing feedback, then allow it.

    next_step = max(0, phase.order) # actually start at the current phase
    all_phases = PRPhase.objects.filter(pr=pr, is_active=True).order_by('order')
    now_time = datetime.datetime.utcnow()
    show_feedback = False
    report = {}
    while (next_step <= all_phases.last().order):
        next_phase = all_phases.filter(order=next_step)
        next_step = next_step + 1
        if (next_phase):
            try:
                feedback_phase = FeedbackPhase.objects.get(id=next_phase[0].id)
            except FeedbackPhase.DoesNotExist:
                continue

            if (feedback_phase.start_dt.replace(tzinfo=None) <= now_time) \
               and (feedback_phase.end_dt.replace(tzinfo=None)>now_time):
                show_feedback = True

            if show_feedback:

                # But wait, the ``learner`` could have kept a link to this
                # peer-review r_actual, and is now trying to access their
                # report.
                group = get_group_information(learner, pr.gf_process)
                if self_review and (r_actual.submission.group_submitted != \
                                    group['group_instance']):
                    if learner.role == 'Learn':
                        # This only counts for learners though.
                        return HttpResponse('This review has expired.')


                if learner.role != 'Learn':
                    # Note: this is not the best, but it allows the admin to
                    # see the reports.
                    learner = r_actual.submission.submitted_by

                # Get the report for this group/learner

                report = get_peer_grading_data(learner, feedback_phase)
                break

    logger.debug('Getting review for {0}:'.format(learner))

    # Intentionally put the order_by here, to ensure that any errors in the
    # next part of the code (zip-ordering) are highlighted
    r_item_actuals = r_actual.ritemactual_set.all().order_by('-modified')

    # Ensure the ``r_item_actuals`` are in the right order. These 3 lines
    # sort the ``r_item_actuals`` by using the ``order`` field on the associated
    # ``ritem_template`` instance.
    # I noticed that in some peer reviews the order was e.g. [4, 1, 3, 2]
    r_item_template_order = (i.ritem_template.order for i in r_item_actuals)
    zipped = list(zip(r_item_actuals, r_item_template_order))
    r_item_actuals, _ = list(zip(*(sorted(zipped, key=lambda x: x[1]))))

    # Small experiment: do rubrics from low to high (+order),  or
    # from high to low (-order), score better or worse?
    #hash_name = hashlib.md5(learner.display_name.encode())
    #digit = re.search("\d", hash_name.hexdigest())
    #if digit:
    #    value = int(hash_name.hexdigest()[digit.start()])
    #else:
    #    value = 0

    # The above code does not work for students with non-ascii characters in
    # their name.
    value = 0
    has_prior_answers = False
    for item in r_item_actuals:
        item_template = item.ritem_template

        if value % 2 == 0: # even
            # from hg revision 200 onwards, both will be ordered from
            # low to high (experiment is over!). Since we sometimes use
            # dropdowns, and this is cleaner without the confused order.
            item.options = ROptionTemplate.objects.filter(\
                                 rubric_item=item_template).order_by('order')
        else:
            item.options = ROptionTemplate.objects.filter(\
                                rubric_item=item_template).order_by('order')


        for option in item.options:
            prior_answer = ROptionActual.objects.filter(roption_template=option,
                                                        ritem_actual=item,
                                                        submitted=True)
            if prior_answer.count():
                has_prior_answers = True
                if item_template.option_type in ('DropD', 'Chcks'):
                    option.selected = True
                elif item_template.option_type == 'LText':
                    option.prior_text = prior_answer[0].comment


        # Store the peer- or self-review results in the item; to use in the
        # template to display the feedback.
        item.results = report.get(item_template, [[], None, None, None, []])

        # Randomize the comments and numerical scores before returning.
        shuffle(item.results[0])
        if item_template.option_type == 'LText':
            item.results[0] = '\n----------------------\n'.join(item.results[0])
            item.results[4] = '\n'.join(item.results[4])


    if has_prior_answers:
        if show_feedback:
            logger.debug('Reviewing-feedback: {0}'.format(learner))
            create_hit(request, item=r_actual, event='reviewing-feedback',
                   user=learner, other_info='Reviewing feedback')
        else:
            logger.debug('Continue-review: {0}'.format(learner))
            create_hit(request, item=r_actual, event='continue-review-session',
                   user=learner, other_info='Returning back')

    else:
        logger.debug('Start-review: {0}'.format(learner))
        create_hit(request, item=r_actual, event='start-a-review-session',
                   user=learner, other_info='Fresh start')

    ctx = {'ractual_code': ractual_code,
           'submission': r_actual.submission,
           'person': learner,
           'r_item_actuals' : r_item_actuals,
           'rubric' : r_actual.rubric_template,
           'show_feedback': show_feedback,
           'report': report,
           'self_review': self_review,
           }
    return render(request, 'review/review_peer.html', ctx)

def process_POST_review(key, options, items):
    """
    Each ``key`` in ``request.POST`` has a list (usually with 1 element)
    associated with it. This function processes that(those) element(s) in the
    list.

    The ``items`` dict, created in the calling function, contains the template
    for each item and its associated options.

    If unsuccessfully processed (because it is an empty ``option``), it will
    return "False" as the 1st returned item.
    """
    r_opt_template = None
    item_number = int(key.split('item-')[1])
    comment = ''
    did_succeed = False
    words = 0
    if items[item_number]['template'].option_type in ('Chcks',):
        prior_options_submitted = ROptionActual.objects.filter(
                                    ritem_actual=items[item_number]['item_obj'])

        prior_options_submitted.delete()

    for value in options:

        if items[item_number]['template'].option_type == 'LText':
            r_opt_template = items[item_number]['options'][0]
            if value:
                comment = value
                words += len(re.split('\s+', comment))
                did_succeed = True
            else:
                # We get for text feedback fields that they can be empty.
                # In these cases we must continue as if they were not filled
                # in.
                #continue
                pass  # <--- this is a better option, incase user wants to
                      #      remove their comment entirely.

        elif items[item_number]['template'].option_type in ('Radio', 'DropD',
                                                             'Chcks'):
            selected = int(value.split('option-')[1])

            # in "selected-1": the '-1' part is critical
            try:
                r_opt_template = items[item_number]['options'][selected-1]
                did_succeed = True
            except (IndexError, AssertionError):
                continue

        if items[item_number]['template'].option_type in ('Radio', 'DropD',
                                                          'LText'):
            # Checkboxes ('Chks') should NEVER DELETE, nor ALTER, the prior
            # ``ROptionActual`` instances for this item type, as you might
            # otherwise see for dropdowns, radio buttons, or text fields.

            # If necessary, prior submissions for the same option are adjusted
            # as being .submitted=False (perhaps the user changed their mind)
            prior_options_submitted = ROptionActual.objects.filter(
                                   ritem_actual=items[item_number]['item_obj'])

            prior_options_submitted.update(submitted=False)


        # Then set the "submitted" field on each OPTION
        ROptionActual.objects.get_or_create(roption_template=r_opt_template,

                            # This is the way we bind it back to the user!
                            ritem_actual=items[item_number]['item_obj'],
                            submitted=True,
                            comment=comment)

        # Set the RItemActual.submitted = True for this ITEM
        items[item_number]['item_obj'].submitted = True
        items[item_number]['item_obj'].save()

    if did_succeed:
        return item_number, r_opt_template.score, words
    else:
        return did_succeed, 0.0, 0


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
    if learner is None:
        # This branch only happens with error conditions.
        return r_actual

    r_item_actuals = r_actual.ritemactual_set.all()

    items = {}
    # Create the dictionary: one key per ITEM.
    # The value associated with the key is a dictionary itself.
    # items[1] = {'options': [....]  <-- list of the options associated
    #             'item_obj': the item instance / object}
    #

    for item in r_item_actuals:
        item_template = item.ritem_template
        item_dict = {}
        items[item_template.order] = item_dict
        item_dict['options'] = item_template.roptiontemplate_set.all()\
                                                          .order_by('order')
        item_dict['item_obj'] = item
        item_dict['template'] = item_template

    # Stores the users selections as "ROptionActual" instances
    word_count = 0
    total_score = 0.0
    for key in request.POST.keys():

        # Small glitch: a set of checkboxes, if all unselected, will not appear
        # here, which means that that item will not be "unset".

        # Process each item in the rubric, one at a time. Only ``item``
        # values returned in the form are considered.
        if not(key.startswith('item-')):
            continue

        item_num, score, words = process_POST_review(key,
                                              request.POST.getlist(key, None),
                                              items)

        # Only right at the end: if all the above were successful:
        if (item_num is not False): # explicitly check, because here 0 \= False
            items.pop(item_num)  # this will NOT pop if "item_num=False"
                                 # which happens if an empty item is processed
        total_score += score
        word_count += words

    # All done with storing the results. Did the user fill everything in?
    if request.POST:
        request.POST.pop('csrfmiddlewaretoken', None) # don't want this in stats
    if len(items) == 0:
        # And once we have processed all options and all items, we can also:
        r_actual.submitted = True
        r_actual.completed = datetime.datetime.utcnow()
        r_actual.status = 'C' # completed
        r_actual.word_count = word_count
        r_actual.score = total_score
        r_actual.save()
        logger.debug('ALL-DONE: {0}'.format(learner))
        create_hit(request, item=r_actual, event='ending-a-review-session',
                   user=learner, other_info='COMPLETE ' + str(request.POST))
    else:
        r_actual.submitted = False
        r_actual.completed = r_actual.started
        r_actual.status = 'P' # In progress
        r_actual.word_count = word_count
        r_actual.save()
        create_hit(request, item=r_actual, event='ending-a-review-session',
                   user=learner, other_info='MISSING {0}'.format(len(items))\
                                                     + str(request.POST)  )
        logger.debug('MISSING[{0}]: {1}'.format(len(items),
                                                learner))


    ctx = {'n_missing': len(items),
           'return_URI_code': ractual_code,
           }
    return render(request, 'review/thankyou_problems.html', ctx)


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

    phase = PRPhase.objects.filter(pr=pr_process)[4]

    import csv
    statsfile = open('results.tsv', 'w')
    writer = csv.writer(statsfile, delimiter='\t')
    writerow = ['Group name','Email','Self-review [6%]','Peer Review[60%]',
                 'Instructor review[26%]','Peer review credit[8%]',
                 'Average grade','C1','C2','C3','C4','C5','C1','C2','C3',
                 'C4','C5']

    writer.writerow(writerow)
    for student in Person.objects.filter(role='Learn'):
        print(student)
        rowwrite = []

        grade_components = GradeComponent.objects.filter(pr=pr_process).\
              order_by('order')
        total_grade = 0.0
        rowwrite.append(student.enrolled_set.all()[0].group.name)
        rowwrite.append(student.email)
        student_grade = {}
        for item in grade_components:

            grade_achieved, grade_detail = get_grading_percentage(item, student)
            total_grade += item.weight * grade_achieved
            student_grade[item.name_in_table] = grade_achieved
            rowwrite.append(str(grade_achieved))

        rowwrite.append(str(total_grade))

        r_template = phase.rubrictemplate_set.all()
        if r_template:
            r_template = r_template[0]

        evals_completed = RubricActual.objects.filter(status='C',
                                                      graded_by=student,
                                                rubric_template=r_template)
        for r_actual in evals_completed:
            for item in r_actual.ritemactual_set.filter(submitted=True)\
                                                            .order_by('id'):
                if item.ritem_template.option_type == 'LText':
                    print(item)
                    rowwrite.append(item.roptionactual_set.all()[0].comment\
                            .encode('utf-8').replace(b'\t', b'').\
                            replace(b'\r\n', b'|').replace(b'\n', b'|'))

        writer.writerow(rowwrite)
        print('------')

    statsfile.close()
    return HttpResponse('The report is on the server to download.')


def get_grading_percentage(item, learner):
    """
    Each ``item.phase`` has an associated grade. This function calculates
    that grade, and returns it, and also the rendered row in the table.
    """
    grade = 0.0
    grade_detail = item.explanation
    ctx = {}
    try:
        if item.phase.feedbackphase:
            report = get_peer_grading_data(learner,
                                           item.phase,
                                           item.extra_detail)
            try:
                learner_total = report.get('learner_total', 0.0)
                overall_max_score = report.get('overall_max_score', 0.0)
                grade =  learner_total / overall_max_score * 100
            except ZeroDivisionError:
                grade = 0.0
            grade_text = '{:0.1f} out of a maximum of {:0.0f} points'.format(\
                    learner_total, overall_max_score)
            ctx['grade_text'] = grade_text
            ctx['n_reviews'] = report['n_reviews']

            grade_detail = Template(item.explanation).render(Context(ctx))

    except PRPhase.DoesNotExist:
        pass

    try:
        if item.phase.peerevaluationphase:
            n_eval=item.phase.peerevaluationphase.number_of_reviews_per_learner
            r_template = item.phase.rubrictemplate_set.all()
            grade = 0.0
            grade_detail = 'An error occured when calculationg this compoent.'
            if r_template:
                r_template = r_template[0]
            else:
                logger.warn('Invalid request: no rubric attached')
                return grade, grade_detail

            n_evals_completed = RubricActual.objects.filter(status='C',
                                        graded_by=learner,
                                        rubric_template=r_template).count()
            ctx['n_evals_completed'] = n_evals_completed
            try:
                grade = n_evals_completed / n_eval * 100
            except ZeroDivisionError:
                grade = 0.0
            grade_detail = Template(item.explanation).render(Context(ctx))

    except PRPhase.DoesNotExist:
        pass

    return grade, grade_detail