from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from review.models import Course, Person

@python_2_unicode_compatible
class Group_Formation_Process(models.Model):
    """ Describes the Group Formation Process: requirements and deadlines.
    """
    class Meta:
        verbose_name = 'Group formation process'
        verbose_name_plural = 'Group formation processes'

    # This can be used to branch code, if needed, for different LTI systems
    CHOICES = (('Brightspace-v1', 'Brightspace-v1'),
               ('edX-v1', 'edX-v1'))

    # Brightspace: HTML-POST: u'lti_version': [u'LTI-1p0'],

    LTI_system = models.CharField(max_length=50, choices=CHOICES,)
    title = models.CharField(max_length=300, verbose_name="Group formation name")
    LTI_id = models.CharField(max_length=50, verbose_name="LTI ID",
        help_text=('In Brightspace LTI post: "resource_link_id"'))

    course = models.ForeignKey(Course)

    instructions = models.TextField(help_text='May contain HTML instructions',
                verbose_name='Overall instructions to learners', )

    # Dates and times
    dt_groups_open_up = models.DateTimeField(
        verbose_name='When can learners start to register', )

    dt_selfenroll_starts = models.DateTimeField(
        verbose_name="When does self-enrolment start?",
        help_text='Usually the same as above date/time, but can be later', )

    dt_group_selection_stops = models.DateTimeField(
        verbose_name=('When does group selection stop'))

    # True/False settings:
    allow_unenroll = models.BooleanField(default=True,
        help_text=('Can learners unenroll, which implies they will also be '
                   'allowed to re-enroll, until the close off date/time.'))

    show_fellows = models.BooleanField(default=False,
        help_text=('Can learners see the FirstName LastName of the other '
                   'people enrolled in their groups.'))

    show_description = models.BooleanField(default=True,
        help_text=('Should we show the group descriptions also?'))

    random_add_unenrolled_after_cutoff = models.BooleanField(default=False,
        verbose_name=('Randomly add unenrolled learners after the cutoff date/time'),
        help_text=('Should we randomly allocate unenrolled users after '
                   'the cut-off date/time ("dt_group_selection_stops")?'))


    def __str__(self):
        return self.title


@python_2_unicode_compatible
class Group(models.Model):
    """ Used when learners work/submit in groups."""
    gp = models.ForeignKey(Group_Formation_Process)
    name = models.CharField(max_length=300, verbose_name="Group name")
    description = models.TextField(blank=True,
                                   verbose_name="Detailed group description")
    capacity = models.PositiveIntegerField(default=0,
        help_text=('How many people in this particular group instance?'))
    order = models.PositiveIntegerField(default=0, help_text=('For ordering '
            'purposes in the tables.'))

    def __str__(self):
        return u'{0}'.format(self.name)


class Enrolled(models.Model):
    """
    Which group is a learner enrolled in"""
    person = models.ForeignKey(Person)
    group = models.ForeignKey(Group, null=True,
        help_text=('If blank/null: used internally to enrol the rest of the '
                                          'class list.'))
    is_enrolled = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
