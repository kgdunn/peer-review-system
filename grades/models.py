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

class GradeItem(models.Model):
    """
    An item in the gradebook. Each gradebook consists of one or more items
    (columns) in the gradebook.
    """
    gradebook = models.ForeignKey(GradeBook)
    order = models.PositiveSmallIntegerField(
                                  help_text="Which column order is this item")
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100,
        help_text="The largest value a student can achieve for this item")
    link = models.CharField(max_length=600, blank=True,
        verbose_name=("The link to the page where the student can complete "
                      "this; begin link after the base URL: /courseware/..."))
    weight = models.DecimalField(max_digits=4, decimal_places=3,
            help_text='The weight of this item; a value between 0.0 and 1.0')

class LearnerGrade(models.Model):
    """
    A grade for the learner.
    """
    gitem = models.ForeignKey(GradeItem)
    learner = models.ForeignKey(Person)
    value = models.DecimalField(max_digits=7, decimal_places=3,
                                help_text="The grade earned by the learner.")





