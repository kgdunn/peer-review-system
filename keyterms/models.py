from django.db import models

# Create your models here.
class BookletSettings(models.Model):
    """
    General settings for a booklet
    """
    n_thumbs = models.PositiveSmallIntegerField(help_text='Maximum number of '
                                           'thumbs up that can be awarded')

    min_submissions_before_voting = models.PositiveSmallIntegerField(
        help_text='Minimum number of submissions before voting can start.')

class KeyTermTask(models.Model):
    """
    The details for learners to fill in 1 new key term.
    """
    keyterm_text = models.CharField(max_length=254)
    deadline_for_voting = models.DateTimeField()
    resource_link_page_id = models.CharField(max_length=50,
        verbose_name="Resource Link Page ID",
        help_text=('LTI post field: "resource_link_id"'))

class Image(models.Model):
    """
    The template image
    """
    person = models.ForeignKey('review.Person')
    link_to_raw = models.ImageField
    link_to_modified = models.ImageField()



