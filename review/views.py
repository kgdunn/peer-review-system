from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from django.views.decorators.clickjacking import xframe_options_exempt

from .models import Person, Course, PR_process

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
    logger.debug('Looking up student')
    if request.POST.get('ext_d2l_token_digest', None):
        name = request.POST['lis_person_name_given']
        email = request.POST['lis_person_contact_email_primary']
        full_name = request.POST['lis_person_name_full']
        user_ID = request.POST['user_id']
        role = request.POST['roles']
        if 'Instructor' in role:
            role = 'Admin'
        elif 'Student' in role:
            role = 'Learn'
    else:
        return None

    logger.debug('About to check: name={0}, email = {1}, full_name = {2}, user_ID = {3}, role = {4}'.format(name, email, full_name, user_ID, role))
    learner, newbie = Person.objects.get_or_create(name=name,
                                                   email=email,
                                                   full_name=full_name,
                                                   role=role)
    if learner:
        # Augments the learner with extra fields that might not be there
        debug.info('Augumated user_ID on %s'.format(learner.email))
        if learner.user_ID == '':
            learner.user_ID = user_ID
            learner.save()

    logger.debug('learner = %s' % str(learner))
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

            ctx = {'person': person_or_error,
                   'course': course,
                   'pr': pr
                  }

            #form = UploadFileForm()
            return render(request, 'review/welcome.html', ctx)#, {'form': form})


        #form = UploadFileForm(request.POST, request.FILES)
        #if form.is_valid():
        #    handle_uploaded_file(request.FILES['file'])
        #    return HttpResponseRedirect('/success')

    else:
        return HttpResponse(("You have reached the Peer Review LTI component "
                                    "without authorization."))



#def manual_create_uploads(request):
    #"""
    #"""
    #name = ''
    #email = ''
    #full_name = ''
    #person = Person(name=name,
                    #is_active = True,
                    #email = email,
                    #full_name = full_name,
                    #user_ID='',
                    #role='Student')

    #status = 'S'
    #pr_process = PR_process.objects.filter(id=1)
    #is_valid = True
    #file_upload = ''
    #submitted_file_name = '/{0}/'.format(pr_process.id)
    #ip_address = '0.0.0.0'

    ##MEDIA_ROOT/nnn/<filename>
    ##    return '{0}'.format(instance.pr_process.id) + os.sep

    #self.photo.save(
        #os.path.basename(self.url),
        #File(open(result[0]))
        #)

    #self.save()
