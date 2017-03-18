from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
import os

# Our imports
from utils import generate_random_token

@python_2_unicode_compatible
class Person(models.Model):
    """
    A learner, with their details provided from the LTI system.
    """
    ROLES = (('Admin', "Administrator"),
             ('Learn', "Learner"),
             ('TA', 'Teaching Assistant')
            )
    is_active = models.BooleanField(default=True, help_text=('NOT USED'))
    email = models.EmailField(blank=False)
    student_number = models.CharField(max_length=15, blank=True, default='')
    display_name = models.CharField(max_length=400, verbose_name='Display name',
                                   blank=True)
    user_ID = models.CharField(max_length=100, blank=True,
                                            verbose_name='User ID from LMS/LTI')
    role = models.CharField(max_length=5, choices=ROLES, default='Learn')

    def __str__(self):
        return u'{0}'.format(self.email)


@python_2_unicode_compatible
class Course(models.Model):
    """ Which courses are being supported."""
    name = models.CharField(max_length=300, verbose_name="Course name")
    label = models.CharField(max_length=300, verbose_name="LTI POST label",
        help_text=("Obtain this from the HTML POST field: 'context_id' "))
    # Brightspace:   u'lis_course_offering_sourcedid': <--- is another option
    #                                  [u'brightspace.tudelft.nl:training-IDE'],
    #
    # edX:   u'context_id': [u'course-v1:DelftX+IDEMC.1x+1T2017']

    offering = models.PositiveIntegerField(default='0000', blank=True,
        help_text="Which year/quarter is it being offered?")

    def __str__(self):
        return u'%s' % self.name


    def save(self, *args, **kwargs):

        super(Course, self).save(*args, **kwargs) # Call the "real" save()


@python_2_unicode_compatible
class PR_process(models.Model):
    """ Describes the Peer Review process: requirements and deadlines.

    There is a one-to-one relationship to the rubric template. So create this
    PR_process first, then link it up later when you create the template.

    There is one of these for each peer review activity. If a course has 3
    peer activities, then there will be 3 of these instances.
    """
    class Meta:
        verbose_name = 'Peer review process'
        verbose_name_plural = 'PR processes'

    # This can be used to branch code, if needed, for different LTI systems
    CHOICES = (('Brightspace-v1', 'Brightspace-v1'),
               ('edX-v1',         'edX-v1'),
               ('Coursera-v1',    'Coursera-v1'))

    # How to identify the LTI consumer?
    # ---------------------------------
    # Brightspace: HTML-POST: u'lti_version': [u'LTI-1p0'],
    # edX:         HTML-POST: resource_link_id contains "edX"

    LTI_system = models.CharField(max_length=50, choices=CHOICES,)
    title = models.CharField(max_length=300, verbose_name="Your peer review title")
    LTI_id = models.CharField(max_length=50, verbose_name="LTI ID",
        help_text=('In Brightspace LTI post: "resource_link_id"'))
    LTI_title = models.CharField(max_length=300, verbose_name="LTI Title",
        help_text=('A title to identify this PR in the database'))


        # Old code:
        #-----------
        # help_text=('In Brightspace LTI post: "resource_link_title"'))
        #
        # That is ideally the case, but Brightspace munges this and only returns
        # the title as it was created in the External Tools section, and not
        # the title of the item created in the Content area.
        #
        # More reliable is "resource_link_id"

    course = models.ForeignKey(Course)
    # rubrictemplate <--- from the One-To-One relationship

    uses_groups = models.BooleanField(default=False,
        help_text=('The workflow and responses are slightly modified if groups '
                   'are used.'))
    gf_process = models.ForeignKey('groups.Group_Formation_Process', blank=True,
                                   default=None, null=True,
        help_text=('Must be specified if groups are being used.'))

    instructions = models.TextField(help_text='May contain HTML instructions',
                verbose_name='Overall instructions to learners', )

    def __str__(self):
        return self.title


def peerreview_directory_path(instance, filename):
    """
    The file will be uploaded to MEDIA_ROOT/uploads/nnn/<filename>
    """
    extension = filename.split('.')[-1]
    filename = generate_random_token(token_length=16) + '.' + extension
    return '{0}{1}{2}{1}{3}'.format('uploads',
                                    os.sep,
                                    instance.pr_process.id,
                                    filename)

# Our models for the phases uses ideas from:
# https://docs.djangoproject.com/en/1.10/topics/db/models/#model-inheritance
@python_2_unicode_compatible
class PRPhase(models.Model):
    """
    A peer review has multiple phases; e.g. file submission; self-evaluation,
    re-submit; peer-evaluation; feedback report.  (5 phases in that example).

    These phases can be ordered, as needed.
    """
    class Meta:
            verbose_name = 'PR phase'
            verbose_name_plural = 'PR phases'

    name = models.CharField(max_length=50, default='... Phase ...')
    pr = models.ForeignKey(PR_process, verbose_name="Peer review")
    order = models.PositiveIntegerField(default=1)
    start_dt = models.DateTimeField(default=timezone.now,
                    verbose_name='Start of this phase',)
    end_dt = models.DateTimeField(default=timezone.now,
                    verbose_name='End of this phase', )
    is_active = models.BooleanField(default=True,
            help_text='An override, allowing you to stage/draft phases.')
    show_dates = models.BooleanField(default=True,
            help_text='Shows the dates in the user view')
    #instructions = models.TextField(default='', blank=True)
    templatetext = models.TextField(default='', blank=True,
                    help_text='The template rendered to the user')


    def __str__(self):
        return '{{{0}}}[{1}] {2}'.format(self.pr, self.order, self.name)


class SubmissionPhase(PRPhase):
    """
    All peer reviews have a submission phase, usually the first step.
    This describes what is needed.
    """
    #show_rubric_prior_to_submission = models.BooleanField(default=False,
            #help_text=('Can learners see the rubric before they submit?'))
    max_file_upload_size_MB = models.PositiveSmallIntegerField(default=10)
    accepted_file_types_comma_separated = models.CharField(default='PDF',
                max_length=100,
                help_text='Comma separated list, for example: pdf, docx, doc')

class SelfEvaluationPhase(PRPhase):
    """
    If a self-evaluation is required...
    """
    pass

class PeerEvaluationPhase(PRPhase):
    """
    If a peer-evaluation is required...
    """
    number_of_reviews_per_learner = models.PositiveIntegerField(default=3,
        help_text='How many reviews must each learner complete?')


class FeedbackPhase(PRPhase):
    """
    Text feedback is shown to the user
    """
    pass

class GradeReportPhase(PRPhase):
    """
    Grade report shown to the user
    """
    pass

@python_2_unicode_compatible
class Submission(models.Model):
    """
    An instance of a submission for a learner/group of learners.

    Old files are kept, but not available for download.<-- remove old submissions

    Show submissions for people in the same group in top/bottom order
    Allow multiple uploads till submission deadline is reached.
    """
    STATUS = (('S', 'Submitted'),
              ('T', 'Submitted late'),
              ('F', 'Finished'),
              ('G', 'Being peer-reviewed/graded'),
              ('N', 'Nothing submitted yet'),
              )

    submitted_by = models.ForeignKey(Person)
    group_submitted = models.ForeignKey('groups.Group', blank=True, null=True,
        default=None, help_text="If a group submission, it links back to it.")
    status = models.CharField(max_length=2, choices=STATUS, default='N')
    pr_process = models.ForeignKey(PR_process, verbose_name="Peer review")
    phase = models.ForeignKey(PRPhase, verbose_name="Attached with which phase",
                              default=None, null=True) #to allow migrations
    is_valid = models.BooleanField(default=False,
        help_text=('Valid if: it was submitted on time, or if this is the most '
                   'recent submission (there might be older ones).'))
    file_upload = models.FileField(upload_to=peerreview_directory_path)
    submitted_file_name = models.CharField(max_length=255, default='')

    number_reviews_assigned = models.PositiveSmallIntegerField(default=0,
        help_text='Number of times this submission has been assigned')

    number_reviews_completed = models.PositiveSmallIntegerField(default=0,
        help_text='Number of times this submission has been completed')

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    datetime_submitted = models.DateTimeField(auto_now_add=True,
        verbose_name="Date and time the learner/group submitted.")

    def __str__(self):
        return '[{0}][assign={1}][cmptd={2}]: {3}'.format(self.pr_process,
                                        self.number_reviews_assigned,
                                        self.number_reviews_completed,
                                        self.submitted_by)


@python_2_unicode_compatible
class RubricTemplate(models.Model):
    """
    Describes the rubric that will be attached to a Peer Review.
    One instance per Peer Review (multiple instances for learners are based
    off this template).

    A Rubric consists of one or more Items (usually a row).
    Items consist of one or more Options (usually columns).

    """
    title = models.CharField(max_length=300, verbose_name="Peer review rubric")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    pr_process = models.ForeignKey(PR_process, default=None, null=True, blank=True)

    # Make this the primary way to access the rubric (through a phase, not a PR)
    phase = models.ForeignKey(PRPhase, default=None, null=True, blank=True)

    general_instructions = models.TextField(default='')

    maximum_score = models.FloatField(default=0.0)

    show_order = models.BooleanField(default=True,
            help_text=('Shows the order numbers. e.g "1. Assess ..."; else '
                       'it just shows: "Assess ..."'))

    def save(self, *args, **kwargs):
        super(RubricTemplate, self).save(*args, **kwargs)

    def __str__(self):
        return u'%s' % self.title


@python_2_unicode_compatible
class RubricActual(models.Model):
    """
    The actual rubric: one instance per learner per submission.

    A submission is allocated to a person for grading. This tracks that:
    the status of it, the grade (only if completed and submitted); the
    ``RubricActual`` instance is also used as a ForeignKey in each
    ``RItemActual``. That way we can quickly pull the evaluated score of the
    rubric from these items.

    A few other handy statistics (score, and word_count) are tracked here,
    to minimize frequent or expensive hits on the database.

    """
    STATUS = (('A', 'Assigned to grader'),
              ('P', 'Progressing...'),
              ('C', 'Completed'))

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    started = models.DateTimeField(verbose_name='When did user start grading?')
    completed = models.DateTimeField(verbose_name='When did user end grading?')
    status = models.CharField(max_length=2, default='A', choices=STATUS)
    submitted = models.BooleanField(default=False,
        help_text='Has been completed reviewed AND submitted by peer grader.')
    graded_by = models.ForeignKey(Person)
    rubric_template = models.ForeignKey(RubricTemplate)
    submission = models.ForeignKey(Submission, null=True)

    # This is used to access the rubric, when graded in an external tab
    unique_code = models.CharField(max_length=16, editable=False, blank=True)

    # These are only valid once ``self.submitted=True``
    score = models.FloatField(default=0.0)
    word_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not(self.unique_code):
            self.unique_code = generate_random_token(token_length=16)
        super(RubricActual, self).save(*args, **kwargs)

    def __str__(self):
        return u'Peer: {0}; Sub: {1}'.format(self.graded_by, self.submission)


@python_2_unicode_compatible
class RItemTemplate(models.Model):
    """
    A (usually a row) in the rubric, containing 1 or more ROptionTemplate
    instances.
    An item corresponds to a criterion, and the peers will select an option,
    and also (probably) comment on the criterion.
    """
    r_template = models.ForeignKey(RubricTemplate)
    #comment_required = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    order = models.IntegerField()
    criterion = models.TextField(help_text=('The prompt/criterion for the row '
                                            'in the rubric'))
    max_score = models.FloatField(help_text='Highest score achievable here')

    TYPE = (('Radio', 'Radio buttons (default)'),
            ('DropD', 'Dropdown of scores'),
            ('Chcks', 'Checkbox options: multiple valid answers'), # no score
            ('LText', 'Long text [HTML Text area]'),
            ('SText', 'Short text [HTML input=text]'),)
    option_type = models.CharField(max_length=5, choices=TYPE, default='Radio')


    def save(self, *args, **kwargs):
        """ Override the model's saving function to do some checks """
        self.max_score = float(self.max_score)
        super(RItemTemplate, self).save(*args, **kwargs)

    def __str__(self):
        return u'%d. %s' % (self.order, self.criterion[0:50])

@python_2_unicode_compatible
class RItemActual(models.Model):
    """
    The actual rubric item for a learner.
    """
    ritem_template = models.ForeignKey(RItemTemplate)
    r_actual = models.ForeignKey(RubricActual) # assures cascading deletes
    comment = models.TextField(blank=True) # comment added by the learner
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    # Has the question been submitted yet? True: user actively clicked the
    # submit button; ``False``: XHR stored answer.
    submitted = models.BooleanField(default=False)

    def __str__(self):
        return u'[Item {0}]'.format(self.ritem_template.order)


@python_2_unicode_compatible
class ROptionTemplate(models.Model):
    """
    A rubric option template (a single cell in the rubric). Usually with
    other options to the left and right of it.
    """
    rubric_item = models.ForeignKey(RItemTemplate)
    score = models.FloatField(help_text='Usually: 1, 2, 3, 4, etc points')
    short_text = models.CharField(max_length=50, default='', blank=True,
            help_text='This text is in the drop down')
    criterion = models.TextField(help_text='A prompt/criterion to the peers',
                                 blank=True)
    order = models.IntegerField()
    # NOTE: the ``order`` is ignored for type ``LText``, as there will/should
    #       only be 1 of those per Item.


    def save(self, *args, **kwargs):
        """ Override the model's saving function to do some checks """
        self.score = float(self.score)
        assert(self.score <= self.rubric_item.max_score)
        super(ROptionTemplate, self).save(*args, **kwargs)

    def __str__(self):
        out = u'[%d] %d. %s' % (self.rubric_item.order,
                                 self.order,
                                 self.criterion)
        return out[0:100]

@python_2_unicode_compatible
class ROptionActual(models.Model):
    """
    The filled in ROptionTemplate by a specific learner.
    Note: an Item has one or more Options (ROptionTemplate) associated with it.
          we will not create an "ROptionActual" for each ROptionTemplate,
          only one ROptionActual is created.
          If the user changes their mind, old ROptionActuals are deleted.
    """
    roption_template = models.ForeignKey(ROptionTemplate)
    ritem_actual = models.ForeignKey(RItemActual, null=True)
    comment = models.TextField(blank=True)
    submitted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return u'%s' % (self.roption_template, )

class GradeComponent(models.Model):
    """
    Each PR process will have 1 or more instances of this model. It tells
    the  ``weight`` value that makes up the final grade. Each weight is
    associated with a ``PRPhase``.
    """
    DETAIL = (('peer',       'peer'),
              ('instructor', 'instructor'))

    pr = models.ForeignKey(PR_process)
    phase = models.ForeignKey(PRPhase)
    order = models.PositiveSmallIntegerField(default=0,
                    help_text="Used to order the display of grade items")
    explanation = models.TextField(max_length=500,
        help_text=('HTML is possible; used in the template. Can include '
                   'template elements: {{self.grade_text}}, {{pr.___}}, '
                   '{{self.n_peers}}, etc'))
    weight = models.FloatField(default = 0.0,
                               help_text=('Values must be between 0.0 and 1.0.',
                                          ' It is your responsibility to make '
                                          'sure the total weights do not sum '
                                          'to over 1.0 (i.e. 100%)'))
    extra_detail = models.CharField(max_length=50, choices=DETAIL, blank=True,
        help_text=('Extra information used to help distinguish a phase. For ',
                   'example, the Peer-Evaluation phase is used for instructors '
                   'as well as peers to evaluate. But the instructor(s) grades '
                   'must get a higher weight. This is used to split the code.'))

    def save(self, *args, **kwargs):
        """ Override the model's saving function to do some checks """
        self.weight = max(0.0, min(1.0, self.weight))
        super(GradeComponent, self).save(*args, **kwargs)

#class ReviewReport(models.Model):
    #"""
    #Used for peer-review reports back to the learner/group.
    #"""
    #created = models.DateTimeField(auto_now_add=True)
    #last_viewed = models.DateTimeField(auto_now=True)
    #learner = models.ForeignKey(Person, null=True, blank=True)
    #group = models.ForeignKey('groups.Group', blank=True, null=True,
        #default=None, help_text="If a group submission, links to group.")
    #phase = models.ForeignKey(PRPhase)
    #rubric_template = models.ForeignKey(RubricTemplate)
    #submission = models.ForeignKey(Submission, null=True)

    ## This is used to access the report in an external tab

    #def save(self, *args, **kwargs):
        #if not(self.unique_code):
            #self.unique_code = generate_random_token(token_length=16)
        #super(ReviewReport, self).save(*args, **kwargs)
