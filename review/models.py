from django.db import models
import datetime
import json
import os
from django.utils.timezone import utc

# Django and Python imports
try:
    import simplejson as json
except ImportError:
    import json
from collections import namedtuple

from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

# Our imports
from utils import unique_slugify, generate_random_token


class Person(models.Model):
    """
    A learner, with their details provided from the LTI system.
    """
    ROLES = (('Admin', "Administrator"),
             ('Learn', "Learner"),
             ('TA', 'Teaching Assistant')
            )
    name = models.CharField(max_length=200, verbose_name="First name")
    is_active = models.BooleanField(default=True, help_text=('Placeholder'))
    email = models.EmailField(unique=True, blank=False)
    full_name = models.CharField(max_length=400, verbose_name='Full name',
                                 blank=True)
    user_ID = models.CharField(max_length=100, verbose_name=('User ID from '
            'Brightspace'), blank=True)
    role = models.CharField(max_length=5, choices=ROLES, default='Learn')

    def __str__(self):
        return '{0} [{1}]'.format(self.name, self.email)


class Group(models.Model):
    """ Used when learners work/submit in groups."""
    name = models.CharField(max_length=300, verbose_name="Group name")


class Course(models.Model):
    """ Which courses are being supported."""
    name = models.CharField(max_length=300, verbose_name="Course name")
    label = models.CharField(max_length=300, verbose_name="LTI POST label",
        help_text=("Obtain this from the HTML POST field: 'context_id' "))
    # Brightspace:   u'lis_course_offering_sourcedid': <--- is another option
    #                                  [u'brightspace.tudelft.nl:training-IDE'],
    slug = models.SlugField(default='', editable=False)

    def __str__(self):
        return self.name


    def save(self, *args, **kwargs):
        #self.slug = slugify(self.name)
        unique_slugify(self, self.name, 'slug')
        super(Course, self).save(*args, **kwargs) # Call the "real" save()


class RubricTemplate(models.Model):
    """
    Describes the rubric that will be attached to a Peer Review.
    The PR_process has a link back to here (not the other way around)
    """
    title = models.CharField(max_length=300, verbose_name="Peer review rubric")
    slug = models.SlugField(default='', editable=False)
    def save(self, *args, **kwargs):
        #self.slug = slugify(self.name)
        unique_slugify(self, self.name, 'slug')
        super(Rubric, self).save(*args, **kwargs) # Call the "real" save()


"""
Handles the rubric templates, rubric and rubric sets.

QTemplate: rubric templates hold the structure of the rubric, such as MCQ,
           short answer. They contain placeholders so different values can
           be filled in.

QActual:   actual rubrics are derived from the QTemplate template. The
           placeholders are filled in with specific values. QActual rubrics
           are only used once, and they are unique to a user. There will
           be many of these in the database.


Some other terminology:
* Question: the question asked of the user
* Grading:  the internal representation of the answer (not shown, used for
            auto-grading)
* Solution: the solution displayed to the user
"""


class QTemplate(models.Model):
    """
    The template for a question.
    """
    question_type = (
        ('tf',       'True/False question'),
        ('mcq',      'Multiple choice question'),
        ('short',    'Short answer question'),
        ('long',     'Long answer question'),
        ('numeric',  'Numeric answer (with specified sensitivity)'),
    )
    # e.g. "The changing heat exchanger", if given explicitly, else it is the first
    # few characters of the question itself.

    name = models.CharField(max_length=250)
    slug = models.CharField(editable=False, max_length=32)

    q_type = models.CharField(max_length=10, choices=question_type)
    max_grade = models.PositiveSmallIntegerField()

    # The question template
    t_question = models.TextField()

    def save(self, *args, **kwargs):
        """ Override the model's saving function to do some checks """
        self.max_grade = float(self.max_grade)

        if not self.slug:
            self.slug = generate_random_token(30)

        # Call the "real" save() method.
        super(QTemplate, self).save(*args, **kwargs)

    def __unicode__(self):
        return '[%s] %s [%s]' % (self.id, self.name[0:50], self.q_type)


class QSet(models.Model):
    """
    Manages sets of rubrics (rubric set)
    """
    name = models.CharField(max_length=250)
    slug = models.SlugField(editable=False)
    announcement = models.TextField(blank=True)

    # Many-to-many? A QTemplate can be part of multiple QSet objects, and a
    #               QSet has multiple QTemplate objects.
    # This lists which rubrics are included, and their relative weight.
    include = models.ManyToManyField(QTemplate, through="Inclusion")

    # Which course is this qset used in???
    #course = models.ForeignKey('course.Course')

    # When are questions first available and finally available for answering?
#    ans_time_start = models.DateTimeField(blank=True, null=True)
#    ans_time_final = models.DateTimeField(blank=True, null=True)


    def save(self, *args, **kwargs):
        """ Override  model's saving function to do some checks """
        # Call the "real" save() method.

        # http://docs.djangoproject.com/en/dev/topics/db/models/
                                            #overriding-predefined-model-methods
        unique_slugify(self, '%s %s %s' % (self.name, self.course.code,
                                           self.course.year), 'slug')

        # happens if the slug is totally unicode characters
        if len(self.slug) == 0:
            raise ValidationError('QSet slug contains invalid characters')


        if self.ans_time_start > self.ans_time_final:
            raise ValidationError('Start time must be earlier than end time.')

        # Call the "real" save() method.
        super(QSet, self).save(*args, **kwargs)


    def __unicode__(self):
        return '%s [%s]' % (self.name, self.course.name)



"""
I need a way to allocate reviews to a learner.
* once allocated, it is remembered (state). So when they come back they see the
  same N = 3 reviews, in the same order, waiting for them.

  class Review:
       * source = Submission
       * reviewer = Person
       * allocated_datetime
       * order = 1, 2, 3, 4, ...?
       *

* The review is allocated out of the pool of all submissions.is_valid and take
  the next available review that:
    * is not from the same group as the reviewer
    * has not already been seen by the reviewer
    * that has the lowest number of allocations so far



"""


class Inclusion(models.Model):
    """
    Captures inclusion for rubrics in a QSet
    """
    qtemplate = models.ForeignKey(QTemplate)
    qset = models.ForeignKey(QSet)
    weight = models.PositiveSmallIntegerField(default=1)  #??

    def save(self, *args, **kwargs):
        """ Override  model's saving function to do some checks """

        previous = Inclusion.objects.filter(qset=self.qset).\
            filter(qtemplate=self.qtemplate)
        if previous:
            raise ValidationError(('This question template is already '
                                   'included in this question set'))

        super(Inclusion, self).save(*args, **kwargs)


    def __unicode__(self):
        return 'Question [id=%d] in QSet "%s"' % (self.qtemplate.id,
                                                  self.qset)


class QActual(models.Model):
    """
    The actual question asked to the user. There are many many of these in
    the database.
    """
    # Question origin
    qtemplate = models.ForeignKey(QTemplate)

    # Which question set was this question used in?
    # Only allow/expect blanks with Previews and unit tests
    qset = models.ForeignKey(QSet, null=True, blank=True)

    # Who is grading this question?
    grader = models.ForeignKey(Person)

    # HTML formatted code that was displayed to the user, so we have an
    # accurate reflection of the question
    as_displayed = models.TextField(blank=True)

    # The user's answer (may be intermediate still)
    given_answer = models.TextField(blank=True)
    # * list of strings: ['tf', 'mcq', 'multi']    <- refers to QTemplate.question_type
    # * string: 'short', 'long', 'numeric'         <- string only
    # * dict: {'fib': '....'; 'peer-eval': '...'}  <- dict of strings

    # A copy of the ``QTemplate.t_grading`` field, but customized for this
    # user. Grading keys for the same question can vary from student to
    # student, depending on their specific question values
    grading_answer = models.TextField(blank=True)

    # The user's comments on the question; user uploaded material
    user_comments = models.TextField(blank=True)

    # Feedback from the student based on the grading. (How does this differ
    # from the above field?)
    #feedback = models.TextField(blank=True, null=True)

    # NOTE: it is a conscious decision not to assign grades to the ``QActual``
    #       objects. We rather assign grades in a ``grades.Grade`` object;
    #       these are smaller and we can deal with grading as a separate
    #       event.
    #grade = models.ForeignKey('grades.Grade', blank=True, null=True)

    # Helps to relate the item to webserver logs, traceability, etc
    last_edit = models.DateTimeField(auto_now=True, blank=True, null=True)

    # Has the question been submitted yet? True: used actively clicked the
    # submit button; ``False``: XHR stored answer.
    is_submitted = models.BooleanField(default=False)

    # Links to the previous and next question in the series
    next_q = models.ForeignKey('self', blank=True, null=True, editable=False,
                               related_name='next_question')
    prev_q = models.ForeignKey('self', blank=True, null=True, editable=False,
                               related_name='prev_question')

    def __unicode__(self):
        if self.qset:
            return u'%s, for user "%s", in %s of course "%s"' % (
                self.qtemplate.name,
                self.user.user.username,
                self.qset.name,
                self.qset.course)
        else:
            return u'%s, for user "%s"' % (
                self.qtemplate.name,
                self.user.user.username)

    def save(self, *args, **kwargs):
        """ Override the model's saving function to do some changes """
        if isinstance(self.var_dict, dict):
            self.var_dict = json.dumps(self.var_dict, sort_keys=True)

        #if self.user_material:
        # TODO(KGD): validate the user's upload is OK

        super(QActual, self).save(*args, **kwargs)

    def qtemplate_id(self, instance):
        return instance.qtemplate.id



class PR_process(models.Model):
    """ Describes the Peer Review process: requirements and deadlines.

    There is one of these for each peer review activity. If a course has 3
    peer activities, then there will be 3 of these instances.
    """
    class Meta:
        verbose_name = 'Peer review process'
        verbose_name_plural = 'PR processes'
    # This can be used to branch code, if needed, for different LTI systems
    CHOICES = (('Brightspace-v1', 'Brightspace-v1'),
               ('edX-v1', 'edX-v1'))

    # Brightspace: HTML-POST: u'lti_version': [u'LTI-1p0'],

    LTI_system = models.CharField(max_length=50, choices=CHOICES,)
    title = models.CharField(max_length=300, verbose_name="Your peer review title")
    LTI_title = models.CharField(max_length=300, verbose_name="LTI title",
        help_text=('In Brightspace LTI post: "resource_link_title"'))
    slug = models.SlugField(default='', editable=False)
    course = models.ForeignKey(Course)
    rubric = models.ForeignKey(QTemplate)

    uses_groups = models.BooleanField(default=False,
        help_text=('The workflow and responses are slightly modified if groups '
                   'are used.'))

    instructions = models.TextField(help_text='May contain HTML instructions',
                verbose_name='Overall instructions to learners', )

    # Date 1: submit their work
    submission_deadline = models.DateTimeField(
        verbose_name='When should learners submit their work by', )

    # Date 2: start reviewing their peers
    peer_reviews_start_by = models.DateTimeField(
        verbose_name='When does the reviewing step open for learners to start?')

    # Date 3: complete the reviews of their peers
    peer_reviews_completed_by = models.DateTimeField(
        verbose_name='When must learners submit their reviews by?')

    # Date 4: receive the reviews back
    peer_reviews_received_back = models.DateTimeField(
        verbose_name='When will learners receive their reviews back?')

    # True/False settings:
    show_rubric_prior_to_submission = models.BooleanField(default=False,
        help_text=('Can learners see the rubric before they submit?'))

    make_submissions_visible_after_review = models.BooleanField(default=False,
       help_text=('Can learners see all submissions from peers after the '
                  'reviewing step?'))


    # To come:
    max_file_upload_size_MB = models.PositiveSmallIntegerField(default=10)
    """
    * limitations of the number of files
    * limits on the file size

    """

    def save(self, *args, **kwargs):
        #self.slug = slugify(self.name)
        unique_slugify(self, self.title, 'slug')
        super(PR_process, self).save(*args, **kwargs) # Call the "real" save()


def peerreview_directory_path(instance, filename):
    # The file will be uploaded to MEDIA_ROOT/nnn/<filename>
    return '{0}'.format(instance.pr_process.id) + os.sep

class Submission(models.Model):
    """
    An instance of a submission for a learner/group of learners.

    TODO: allow multiple files as a submission.

    Old files are kept, but not available for download.
    Show submissions for people in the same group in top/bottom order
    Allow multiple uploads till submission deadline is reached.
    """
    STATUS = (('S', 'Submitted'),
              ('T', 'Subitted late'),
              ('F', 'Finished'),
              ('G', 'Being peer-reviewed/graded'),
              ('N', 'Nothing submitted yet'),
              )

    submitted_by = models.ForeignKey(Person)
    status = models.CharField(max_length=2, choices=STATUS, default='N')
    pr_process = models.ForeignKey(PR_process, verbose_name="Peer review")
    is_valid = models.BooleanField(default=False,
        help_text=('Invalid if it is too late, or if a newer submission'
                   'is replacing this one.'))
    file_upload = models.FileField(upload_to=peerreview_directory_path)
    submitted_file_name = models.CharField(max_length=255, default='')

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    datetime_submitted = models.DateTimeField(auto_now_add=True,
        verbose_name="Date and time the learner/group submitted.")


    # Many to one, or one to many??
    #allocated_to = models.ForeignKey(Review)






