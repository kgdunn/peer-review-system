#from django.utils import timezone
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from datetime import timedelta

def get_deadline():
    return now() + timedelta(days=20)

@python_2_unicode_compatible
class KeyTerm_Task(models.Model):
    """
    The details for learners to fill in 1 new key term.
    """

    class Meta:
        verbose_name = "Key Term Task"
        verbose_name_plural = "Key Term Tasks"



    max_thumbs = models.PositiveSmallIntegerField(default=3,
                help_text='Maximum number of thumbs up that can be awarded')
    min_submissions_before_voting = models.PositiveSmallIntegerField(default=10,
        help_text='Minimum number of submissions before voting can start.')
    keyterm_text = models.CharField(max_length=254)
    deadline_for_voting = models.DateTimeField(default=get_deadline)
    resource_link_page_id = models.CharField(max_length=50,
        verbose_name="Resource Link Page ID",
        help_text=('LTI post field: "resource_link_id"'))

    def __str__(self):
        return u'{0}'.format(self.keyterm_text)


@python_2_unicode_compatible
class KeyTerm_Definition(models.Model):
    """
    The KeyTerm defined by a learner in the course.
    """
    class Meta:
        verbose_name = "Key Term Definition"
        verbose_name_plural = "Key Term Definitions"

    keyterm_required = models.ForeignKey(KeyTerm_Task)
    person = models.ForeignKey('review.Person')
    image_raw = models.ImageField(blank=True, null=True)
    image_modified = models.ImageField(blank=True, null=True)
    image_thumbnail = models.ImageField(blank=True, null=True)
    last_edited = models.DateTimeField(auto_now=True, auto_now_add=False)
    definition_text = models.CharField(max_length=505, blank=True, null=True,
                                       help_text='Capped at 500 characters.')
    explainer_text = models.TextField(blank=True, null=True)
    reference_text = models.CharField(max_length=250, blank=True, null=True)
    allow_to_share = models.BooleanField(help_text=('Student is OK to share '
                                                    'their work with class.'),
                                         default=True)
    is_finalized = models.BooleanField(help_text=('User has submitted, and it '
                                                  'is after the deadline'),
                                       default=False)
    #is_submitted = models.BooleanField(help_text=('User has added stuff'))
    #is_locked = models.BooleanField(help_text=('User has not confirmed, but it'
    #                                           'is after the deadline now.'))

    def __str__(self):
        return u'[{0}] defined by {1} on {2:%Y-%m-%d %H:%M}'.format(\
            self.keyterm_required, self.person, self.last_edited)


    def save(self, *args, **kwargs):
        if self.definition_text and (len(self.definition_text)>=500):
            self.definition_text = self.definition_text[0:501] + ' ...'

        super(KeyTerm_Definition, self).save(*args, **kwargs)


@python_2_unicode_compatible
class Thumbs(models.Model):
    """
    Rating for each submission.
    """
    class Meta:
        verbose_name = "Thumbs up"
        verbose_name_plural = "Thumbs up"

    keyterm_definition = models.ForeignKey(KeyTerm_Definition)
    voter = models.ForeignKey('review.Person')
    awarded = models.BooleanField(default=False)
    last_edited = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return u'Thumb up for [{1}] by person {2}'.format(self.person,
                                                    self.keyterm_definition,)



