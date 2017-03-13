from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from review.models import Person

@python_2_unicode_compatible
class Timer(models.Model):
    """General timing statistics about the site usage are summarized here."""
    event_type = (
        ('login', 'login'),
        ('start-a-review-session',    'start-a-review-session'),
        ('ending-a-review-session',   'ending-a-review-session'),
                  )
    event = models.CharField(max_length=80, choices=event_type)

    ua_string = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    referrer = models.CharField(max_length=511, blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Person, blank=True, null=True)
    item_name = models.CharField(max_length=100, blank=True, null=True)
    item_pk = models.PositiveIntegerField(blank=True, null=True, default=0)
    other_info = models.CharField(max_length=5000, blank=True, null=True,
                                  default=None)

    def __str__(self):
        return '%s [%s]' % (self.event, self.user)


