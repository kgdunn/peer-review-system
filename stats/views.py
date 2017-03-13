# Django and Python import
import hashlib
from django.shortcuts import HttpResponse

# Our models
from .models import Timer
from utils import get_IP_address


def create_hit(request, item=None, event='', user=None, other_info=None):
    """
    Given a Django ``request`` object, create an entry in the DB for the hit.

    """
    ip_address = get_IP_address(request)
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    referrer = request.META.get('HTTP_REFERER', None)

    try:
        page_hit = Timer(ip_address=ip_address,
                         ua_string=ua_string,
                         item_name=item._meta.model_name,
                         item_pk=item.pk,
                         other_info=other_info,
                         user=user,
                         event=event)

        page_hit.save()
    except Exception:
        pass


    #event = (
        #('login', 'login'),
        #('start-a-review-session',    'start-a-review-session'),
        #('ending-a-review-session',   'ending-a-review-session'),
    #)