from django.db import models
import datetime
import json
import os
from django.utils.timezone import utc
from django.utils.text import slugify

class Person(models.Model):
    """
    A learner, with their details provided from the LTI system.
    """
    name = models.CharField(max_length=200, verbose_name="First name")
    is_active = models.BooleanField(default=True, help_text=('Placeholder'))
    email = models.EmailField(unique=True)
    def __str__(self):
        return '{0} [{1}]'.format(self.name, self.email)

class Group(models.Model):
    """ Used when learners work/submit in groups."""
    name = models.CharField(max_length=300, verbose_name="Group name")

class Course(models.Model):
    """ Which courses are being supported."""
    name = models.CharField(max_length=300, verbose_name="Course name")
    label = models.CharField(max_length=300, verbose_name="LTI POST label")
    # Brightspace:   u'lis_course_offering_sourcedid':
    #                                  [u'brightspace.tudelft.nl:training-IDE'],
    slug = models.SlugField(default='')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Course, self).save(*args, **kwargs) # Call the "real" save()

class Rubric(models.Model):
    """
    Describes the rubric that will be attached to a Peer Review.
    The PR_process has a link back to here (not the other way around)
    """
    title = models.CharField(max_length=300, verbose_name="Peer review rubric")
    slug = models.SlugField(default='')
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Rubric, self).save(*args, **kwargs) # Call the "real" save()

class PR_process(models.Model):
    """ Describes the Peer Review process: requirements and deadlines.

    There is one of these for each peer review activity. If a course has 3
    peer activities, then there will be 3 of these instances.
    """
    # This can be used to branch code, if needed, for different LTI systems
    CHOICES = (('Brightspace-v1', 'Brightspace-v1'),
               ('edX-v1', 'edX-v1'))

    # Brightspace: HTML-POST: u'lti_version': [u'LTI-1p0'],

    LTI_system = models.CharField(max_length=50, choices=CHOICES,)
    title = models.CharField(max_length=300, verbose_name="Peer review")
    slug = models.SlugField(default='')
    course = models.ForeignKey(Course)
    rubric = models.ForeignKey(Rubric)

    instructions = models.TextField(help_text='May contain HTML instructions',
                verbose_name='Overall instructions to learners', )

    # Date 1: submit their work
    submission_deadline = models.DateTimeField(
        verbose_name='When should learners submit their work by', )

    # Date 2: start reviewing their peers
    peer_reviews_start_by = models.DateTimeField(
        verbose_name='When does the reviewing step open?')

    # Date 3: complete the reviews of their peers
    peer_reviews_completed_by = models.DateTimeField(
        verbose_name='When must learners submit their reviews by?')

    # Date 4: receive the reviews back
    peer_reviews_received_back = models.DateTimeField(
        verbose_name='When will learners receive their reviews back?')

    # True/False settings:
    show_rubric_prior_to_submission = models.BooleanField(default=False,
        help_text=('Can learners see the rubric before they submit?'))

    all_submissions_visible_after_review = models.BooleanField(default=False,
       help_text=('Can learners see all submissions from peers after the '
                  'reviewing step?'))


    # To come:
    """
    * limitations of the number of files
    * limits on the file size

    """

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(PR_process, self).save(*args, **kwargs) # Call the "real" save()


def peerreview_directory_path(instance, filename):
    # The file will be uploaded to MEDIA_ROOT/nnn/<filename>
    return '{0}'.format(instance.pr_process.id) + os.sep

class Submission(models.Model):
    """
    An instance of a submission for a learner/group of learners.

    TODO: allow multiple files as a submission.
    """
    learner = models.ForeignKey(Person)
    pr_process = models.ForeignKey(PR_process)
    file_upload = models.FileField(upload_to=peerreview_directory_path)