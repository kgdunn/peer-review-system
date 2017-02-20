from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from django.views.decorators.clickjacking import xframe_options_exempt

# Our imports
from .models import Person, Course, PR_process, Submission
from .models import RubricActual, ROptionActual, RItemActual
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
        name = request.POST['lis_person_name_given']
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
    #user_ID = {3}, role = {4}'.format(name, email, full_name, user_ID, role))
    learner, newbie = Person.objects.get_or_create(name=name,
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

@csrf_exempt
def success(request):
    logger.debug('Success')
    return HttpResponse("You have successfully uploaded")


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

                # 1get_next_submission_to_evaluate(pr, learner)
                # 2get_rubric_template
                rub_actual, new_rubric = RubricActual.objects.get_or_create(\
                                            graded_by=learner,
                                            rubric_template=pr.rubric)


                if new_rubric:
                    pass
                    # create >=1  RItemActuals here and save






            # STEP 3: after the time when feedback is available?
            # Code her to display the results


            #form = UploadFileForm()
            ctx = {'person': person_or_error,
                   'course': course,
                   'pr': pr
                   }
            return render(request, 'review/welcome.html', ctx)#, {'form': form})


        #form = UploadFileForm(request.POST, request.FILES)
        #if form.is_valid():
        #    handle_uploaded_file(request.FILES['file'])
        #    return HttpResponseRedirect('/success')

    else:
        return HttpResponse(("You have reached the Peer Review LTI component "
                                    "without authorization."))


def manual_create_uploads(request):
    """
    Manually upload the submissions for Conny Bakker IO3075 Aerobics Peer Review
    """

    import csv

    classlist = {}
    with open('/Users/kevindunn/DELETE/IO3075-classlist.csv', 'rt') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            print(row)

            classlist[row[2] + ' ' + row[1]] = (row[2], row[3])

    folder = '/Users/kevindunn/DELETE/Hand in Aerobics Example Download 18 February, 2017 0707.zip Folder'
    import os
    from os.path import join, getsize
    for root, dirs, files in os.walk(folder):
        if files[0].lower().endswith('.pdf'):
            print('PDF')
        else:
            print(files[0])

        #if 'CVS' in dirs:
        #    dirs.remove('CVS')  # don't visit CVS directories

    name = 'Aine '
    email = 'A.M.Cronin@student.tudelft.nl'
    full_name = 'Aine Cronin'
    learner, newbie = Person.objects.get_or_create(name=name,
                                                    email = email,
                                                    full_name = full_name,
                                                    role='Student')
    learner.save()
    logger.debug("Creating submission for %s" % learner)

    status = 'S'
    pr_process = PR_process.objects.filter(id=1)[0]
    is_valid = True
    filename = 'abc.pdf'
    extension = filename.split('.')[-1]
    submitted_file_name = 'uploads/{0}/{1}'.format(pr_process.id,
                    generate_random_token(token_length=16) + '.' + extension)
    ip_address = '0.0.0.0'

    sub = Submission(submitted_by = learner,
                     status = status,
                     pr_process = pr_process,
                     is_valid = True,
                     file_upload = '',
                     submitted_file_name = 'Aine_Cronin_TowardsCircularDesign.pdf',
                     ip_address = ip_address,
                    )

