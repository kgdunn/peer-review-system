from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from review.models import Course, Person

@python_2_unicode_compatible
class GradeBook(models.Model):
    """
    A gradebook for a course.
    """
    course = models.ForeignKey(Course)
    passing_value = models.DecimalField(max_digits=5, decimal_places=2,
                                        help_text="A value between 0 and 100.")
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100,
        help_text="A value between 0 and 100. Normally this is 100.0")
    last_updated = models.DateTimeField()
    def __str__(self):
        return 'Gradebook: {0} [{1}/{2}]'.format(self.course,
                                                 self.passing_value,
                                                 self.max_score)

# Our models for the phases uses ideas from:
# https://docs.djangoproject.com/en/1.10/topics/db/models/#model-inheritance
@python_2_unicode_compatible
class GradeCategory(models.Model):
    """
    A category contains one or more GradeItems. A gradebook consists of
    GradeCategories.
    A GradeItem must be a child of GradeCategory, which is a child of the
    Gradebook.
    """
    class Meta:
        verbose_name = 'Grade Category'
        verbose_name_plural = 'Grade Categories'

    gradebook = models.ForeignKey(GradeBook)
    order = models.PositiveSmallIntegerField(
        help_text="Which column order is this item")
    display_name = models.CharField(max_length=250, default='Assignment ...')
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100,
        help_text="The largest value a student can achieve for this item")
    weight = models.DecimalField(max_digits=4, decimal_places=3,
            help_text='The weight of this item; a value between 0.0 and 1.0')
    spread_evenly = models.BooleanField(default=True,
        help_text=("Spread weight across all items evenly. True: no need to "
                   "specify weights on the GradeItems. "))

    def __str__(self):
        return '{0}. Category: {1} [wt={2}%]'.format(self.order,
                                                    self.display_name,
                                                    self.weight*100)

@python_2_unicode_compatible
class GradeItem(models.Model):
    """
    An item in the gradebook. Each gradebook consists of one or more items
    (columns) in the gradebook.
    """
    category = models.ForeignKey(GradeCategory, blank=True, null=True)
    order = models.PositiveSmallIntegerField(
        help_text="Which column order is this item")
    display_name = models.CharField(max_length=250, default='Assignment ...')
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100,
        help_text="The largest value a student can achieve for this item")
    link = models.CharField(max_length=600, blank=True,
           help_text=("The link to the page where the student can complete "
                      "this; begin link after the base URL: /courseware/..."))
    weight = models.DecimalField(max_digits=4, decimal_places=3, default=-1.0,
                                 blank=True,
            help_text=('The weight of this item; a value between 0.0 and 1.0. '
                    'If weight=-1.0, then the weight is determined by the '
                    'category, which will assign equal weight to all items.'))
    droppable = models.BooleanField(default=False)


    def __str__(self):
        return '{0}. Category: {1}'.format(self.order,
                                           self.display_name)


@python_2_unicode_compatible
class LearnerGrade(models.Model):
    """
    A grade for the learner.
    """
    gitem = models.ForeignKey(GradeItem)
    learner = models.ForeignKey(Person)
    value = models.DecimalField(max_digits=7, decimal_places=3, blank=True,
                                null=True,
                                help_text="The grade earned by the learner.")
    not_graded_yet = models.BooleanField(default=True,
            help_text="If this item is not yet graded/submitted/etc")
    modfied_dt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '[{0}/{1}] for {2}'.format(self.value,
                                          self.gitem.max_score,
                                          self.learner)






