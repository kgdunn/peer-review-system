from django.template.defaultfilters import slugify
from django.conf import settings
from django.core.mail import BadHeaderError
from django.core.mail import send_mail as _send_mail
from django.core.mail import send_mass_mail
from django.template import Context, Template
from pygments import formatters, highlight, lexers

import re
import os
import errno
import logging
import datetime

email_from = settings.DEFAULT_FROM_EMAIL
logger = logging.getLogger(__name__)

rest_help_extra = """Use <a href="http://sphinx.pocoo.org/latest/rest.html">reStructuredText</a>.
<div class="spc-markup-help"><ul>
<li class="spc-odd">Use linebreaks between paragraphs</li>
<li class="spc-even"><tt>*</tt><i>italics</i><tt>*</tt> and <tt>**</tt><b>bold</b><tt>**</tt></li>
<li class="spc-odd"><tt>`Hyperlinks &lt;http://example.com&gt;`_</tt></li>
<li class="spc-even"><tt>``monospaced text``</tt></li>
<li class="spc-odd"><tt>\(</tt><tt>e^{i \pi}+1=0</tt><tt>\)</tt> shows as \(e^{i \pi}+1=0\)</li>
<li class="spc-even"><a href="/markup-help" target="_blank">More help</a> with bulleted lists, math, hyperlinks and other features</li>
</div>"""



def ensuredir(path):
    """Ensure that a path exists."""
    # Copied from sphinx.util.osutil.ensuredir(): BSD licensed code, so it's OK
    # to add to this project.
    EEXIST = getattr(errno, 'EEXIST', 0)
    try:
        os.makedirs(path)
    except OSError as err:
        # 0 for Jython/Win32
        if err.errno not in [0, EEXIST]:
            raise

def get_IP_address(request):
    """
    Returns the visitor's IP address as a string given the Django ``request``.
    """
    # Catchs the case when the user is on a proxy
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if ip == '' or ip.lower() in ('unkown', ):
        ip = request.META.get('REMOTE_ADDR', '')   # User is not on a proxy
    if ip == '' or ip.lower() in ('unkown', ):
        ip = request.META.get('HTTP_X_REAL_IP')
    return ip

# From: http://djangosnippets.org/snippets/690/
def unique_slugify(instance, value, slug_field_name='slug', queryset=None,
                   slug_separator='-'):
    """
    Calculates and stores a unique slug of ``value`` for an instance.

    ``slug_field_name`` should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).

    ``queryset`` usually doesn't need to be explicitly provided - it'll default
    to using the ``.all()`` queryset from the model's default manager.
    """
    slug_field = instance._meta.get_field(slug_field_name)

    slug = getattr(instance, slug_field.attname)
    slug_len = slug_field.max_length

    # Sort out the initial slug, limiting its length if necessary.
    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    # Create the queryset if one wasn't explicitly provided and exclude the
    # current instance from the queryset.
    if queryset is None:
        queryset = instance.__class__._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    # Find a unique slug. If one matches, add '-2' to the end and try again
    # (then '-3', etc).
    next_try = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = '%s%s' % (slug_separator, next_try)
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[:slug_len-len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = '%s%s' % (slug, end)
        next_try += 1

    setattr(instance, slug_field.attname, slug)

def _slug_strip(value, separator='-'):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.

    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.
    """
    separator = separator or ''
    if separator == '-' or not separator:
        re_sep = '-'
    else:
        re_sep = '(?:-|%s)' % re.escape(separator)
    # Remove multiple instances and if an alternate separator is provided,
    # replace the default '-' separator.
    if separator != re_sep:
        value = re.sub('%s+' % re_sep, separator, value)
    # Remove separator from the beginning and end of the slug.
    if separator:
        if separator != '-':
            re_sep = re.escape(separator)
        value = re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)
    return value

def highlight_code(code, lexer=None):
    """ Uses Pygments to provide syntax highlighting.
    By default, the highlighting assumes Python code.
    """
# See this page for help with colouring: http://pygments.org/docs/tokens/
#
#from pygments.styles.default import DefaultStyle
#from pygments.style import Style
#from pygments.styles import get_style_by_name
#from pygments.token import Comment, Keyword, Name, String, Operator, Number
#from pygments import formatters
#class SciPyStyle(Style):
    #default_style = ""
    #styles = {
            ##Comment:                '#888',
            ##Keyword:                'bold #080',
            ##Name:                   '#080',
            ##Name.Function:          '#00F',
            ##Name.Class:             'bold #00F',
            ##String:                 '#BA2121',
            #Comment:                '#008000',
            #Keyword:                'bold #000080',
            #Name:                   '#000',
            #Name.Builtin:           '#407090',
            #Name.Function:          'bold #008080',
            #Name.Class:             'bold #00F',
            #Name.Namespace:         '#000000',
            #Number:                 '#008080',
            #String:                 '#800080',
            #String.Doc:             '#800000',
            #Operator:               '#000000',
            #Operator.Word:          'bold #AA22FF',
    #}

#formatter = formatters.HtmlFormatter(style=SciPyStyle)
#print(formatter.get_style_defs('.highlight'))

    if code is None:
        return None
    else:
        lexer_class = lexers.get_lexer_for_mimetype(lexer or 'text/x-python')
        return highlight(code, lexer_class,
                         formatters.HtmlFormatter(linenos=True,
                                                  linenostep=1,))

def send_email(to_addresses, subject, messages):
    """
    Basic function to send email according to the four required string inputs.
    Let Django send the message; it takes care of opening and closing the
    connection, as well as locking for thread safety.

    If ``messages`` is a list and ``to_addresses`` is a list and both are of
    the same length, then it uses Django's mass emailing function, where
    the subject is re-used for all messages.
    """
    from_address = email_from
    to_list = []
    if from_address is None:
        from_address = settings.SERVER_EMAIL

    if isinstance(to_addresses, list) and isinstance(messages, list):

        if len(to_addresses) == len(messages):
            data = []
            for idx, message in enumerate(messages):
                if settings.DEBUG:
                    data.append((subject, message, from_address,
                                                     ['test@example.com',]))
                    to_list.append('test@example.com')
                else:
                    data.append((subject, message, from_address,
                                                     [to_addresses[idx],]))
                    to_list.append(to_addresses[idx])

        use_mass_email = True
    else:
        use_mass_email = False
        if settings.DEBUG:
            logger.debug('Overwriting the email: sending to @example.com.')
            # Overwrite sender address in debug mode
            to_addresses = ['test@example.com',]
            to_list.append('test@example.com')

    out = None
    if use_mass_email:
        try:
            out = send_mass_mail(tuple(data), fail_silently=False)
        except Exception as e:
            logger.error(('An error occurred when sending mass emails [%s]' %
                          str(e)))
    else:
        if subject and messages and from_address:
            try:
                out = _send_mail(subject, messages, from_address, to_addresses,
                                 fail_silently=False)
            except Exception as e:
                logger.error(('An error occurred when sending email to %s, '
                              'with subject [%s]. Error = %s') % (
                                  str(to_addresses),
                                  subject,
                                  str(e)))

    return out, to_list

def generate_random_token(token_length=16, base_address='', easy_use=False):
    import random

    if easy_use:
        # use characters from a restricted range, that are easy to write and read
        # unambiguously
        token = ''.join([random.choice(('abfghkqstwxyz2345689'))
                                               for i in range(token_length)])
    else:
        token = ''.join([random.choice(('ABCEFGHJKLMNPQRSTUVWXYZ'
                                            'abcdefghjkmnpqrstuvwxyz2345689'))
                                                       for i in range(token_length)])
    return base_address + token



def insert_evaluate_variables(text, var_dict):
    """
    Uses the Django template library to insert and evaluate expressions.
    A list of strings and the variable dictionary of key-value pairs to
    insert must be provided.
    """
    if isinstance(text, list):
        text.insert(0, '{% load quest_render_tags %}')
        rndr_string = '\n'.join(text)
    else:
        rndr_string = r'{% load quest_render_tags %} ' + text

    var_dict_rendered = {}
    for key, values in var_dict.iteritems():
        var_dict_rendered[key] = values[1]

    tmplte = Template(rndr_string)
    cntxt = Context(var_dict_rendered)
    return tmplte.render(cntxt)

def grade_display(actual, max_grade):
    """
    Nicely formats the grades for display to the user
    """
    def formatter(value):
        if round(value, 8) == round(value,0):
            return '%0.0f' % value
        else:
            return '%0.1f' % value

    if actual is not None:
        return '%s/%s' % (formatter(actual), formatter(max_grade))
    else:
        return '%s' % formatter(max_grade)


def merge_dicts(primary, secondary, deepcopy=False):
    """ This helper function will merge dictionary keys and their values.

        The `primary` keys are always kept and override the `secondary` keys.
        Any `secondary` keys that do not appear in `primary` are also added.
        The joint dictionary is returned.

        Note: by default, a shallow copy (reference copy) of secondary is made.
        You can force a deepcopy by setting the input argument, `deepcopy` to
        True.
    """
    # Objective: assemble `out` from
    # (1) `primary`     <has a higher priority>
    # (2) `secondary`

    out = {}
    if deepcopy:
        two = _copy.deepcopy(secondary)
    else:
        two = secondary.copy()
    out.update(primary)

    # Remove those same keys from `secondary`:
    for key in primary.iterkeys():
        two.pop(key, None)

    # Then append any remaining values in `secondary` into `out`.  However
    # first deepcopy those values, if we've been asked to:
    if deepcopy:
        out.update(_copy.deepcopy(two))
    else:
        out.update(two)
    return out
