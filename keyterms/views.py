from django.shortcuts import render
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt

# Imports from other applications
# -------------------------------
from review.views import starting_point, recognise_LTI_LMS
from review.models import Person, Course
from stats.views import create_hit


# Imports for this application
from .models import KeyTerm_Definition, KeyTerm_Task, Thumbs


# Logging
import logging
logger = logging.getLogger(__name__)


# Use the "{% load thumbnail %}" from http://sorl-thumbnail.readthedocs.io/en/latest/index.html

# assemble a single PDF from image, text

# Render to PNG
# http://pillow.readthedocs.io/en/3.1.x/reference/ImageDraw.html

# Have a queue to process the image?


def vote_for_keyterm(request):
    """Learning is voting"""
    # Are they allowed to vote?
    # Record vote




def render_keyterm():
    """
    Renders the keyterm image, with text, etc
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, portrait
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph


    image = KeyTerm_Definition.objects.all()[0]


    imagefile = image.image_raw.file.name


    # Thumbnail
    from PIL import Image, ImageDraw
    size = (256, 256)
    imagefile = '/Users/kevindunn/Desktop/Screen Shot 2017-07-16 at 10.31.37.png'
    im = Image.open(imagefile)
    im.thumbnail(size)
    im.save(imagefile + ".jpg", "JPEG")


    # Puts an X over the image
    imagefile = '/var/www/yint.org/static/flipped-mooc/LTS-talk/assets/AE3B29B8-5801-483E-A563-AB8193484613/assets/12303DA0D10FEF5E36D814059432DFAB.png.jpg'
    from PIL import Image, ImageDraw
    im = Image.open(imagefile)
    draw = ImageDraw.Draw(im)
    draw.line((0, 0) + im.size, fill=128)
    draw.line((0, im.size[1], im.size[0], 0), fill=128)
    del draw

    # write to stdout
    im.save(imagefile, "JPEG")


        # Create PNG and add text to it
    from PIL import Image, ImageDraw, ImageFont
    # get a font
    fnt = ImageFont.truetype('Verdana.ttf', 40)
    imagefile = '/var/www/yint.org/static/flipped-mooc/LTS-talk/assets/AE3B29B8-5801-483E-A563-AB8193484613/assets/12303DA0D10FEF5E36D814059432DFAB.png'
    base = Image.open(imagefile).convert('RGBA')

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', base.size, (255,255,255,0))



    # get a drawing context
    d = ImageDraw.Draw(txt)

    # draw text, half opacity
    d.text((10,10), "Hello", font=fnt, fill=(255,255,255,128))
    # draw text, full opacity
    d.text((10,60), "World", font=fnt, fill=(255,255,255,255))

    out = Image.alpha_composite(base, txt)

    out.save(imagefile+'new.png', "PNG")


    full_path = '/Users/kevindunn/Voorwaarden-2016-Basis-Budget-Zeker-Exclusief-90482-1601.pdf'
    extension = 'pdf'
    try:
        c = canvas.Canvas(full_path, pagesize=A4, )
        c.setPageSize(portrait(A4))

        c.setFont("Helvetica", 36)


        p = Paragraph(ptext, self.styles["Normal"])
        p.wrapOn(self.c, self.width-70, self.height)
        p.drawOn(self.c, *self.coord(20, voffset+48, mm))

        styles = getSampleStyleSheet()
        doc = FourBySixNotecard("phello2.pdf", "Test Title", "Andrew Frink")
        Story = []
        p = Paragraph("Title", styles["title"])

        drawString(1*cm, (29.7-2)*cm, 'Third Culture Kids')
        c.drawImage(imagefile,
                    x=cm*0, y=10*cm,
                    width=cm*(21.0-2), height=cm*(29.7-2-17.0),
                    mask=None,
                    preserveAspectRatio=True,
                    anchor='c')
        c.showPage()
        c.save()
    except IOError as exp:
        logger.error('Exception: ' + str(exp))
        # TODO: raise error message


    from wand.image import Image
    imageFromPdf = Image(filename=full_path)
    image = Image(width=imageFromPdf.width, height=imageFromPdf.height)
    image.composite(imageFromPdf.sequence[0], top=0, left=0)
    image.format = "png"
    thumbnail_full_name = full_path.replace('.'+extension, '.png')
    image.save(filename=thumbnail_full_name)

    return 'Success'






def resume_or_fill_in_keyterm(request, terms_per_page, learner):
    """
    Form where the user fills in the required keyterm. They are either resuming
    a prior attempt, or starting from fresh.

    User must first Preview before being allowed to Submit.
    """
    # User could be coming here the first time, previewing, or about to finalize
    # their keyterm.

    _, course, pr = starting_point(request)
    action = request.POST.get('action', '')
    ctx = {'learner': learner, 'course': course, 'pr': pr,
           'action': action}

    if action == '':     # First time here
        ctx['action'] = 'editing'


    # Load what we have from the UI
    definition = request.POST.get('definition', '<No definition supplied>')

    if action == 'preview':

        # Save what we have to the DB;
        keyterm_req = KeyTerm_Task.objects.filter(\
                                           resource_link_page_id=pr.LTI_id)[0]

        term, created = KeyTerm_Definition.objects.get_or_create(person=learner,
                                                keyterm_required=keyterm_req)
        term.definition_text = definition
        term.explainer_text = 'def'
        term.reference_text = 'fge'
        term.allow_to_share = False
        term.is_finalized = False
        term.image_raw = None
        term.save()
        ctx['action'] = 'preview'

        # If a field not provided, then don't allow to be finalized
        #ctx['action'] = 'editing'
        ctx['error_message'] = 'blah'

    # Load what we have in the DB, if anything. Only during 'editing'
    if (terms_per_page.filter(person=learner, is_finalized=False).count()>0):
        term = terms_per_page.filter(person=learner, is_finalized=False)[0]

        ctx['definition'] = term.definition_text


    if action == 'finalize':
        term = terms_per_page.filter(person=learner, is_finalized=False)[0]
        term.is_finalized = True
        term.save()


    # All done, now return the HTML
    return render(request, 'keyterms/form-entry.html', ctx)



def show_vote_keyterms(request, terms_per_page, learner):
    """
    Show the prior key terms for this page. Allow person to vote on them.
    """
    # Always show the users own term, plus those which are shared.
    terms = terms_per_page.filter(Q(person=learner) |  \
                                  Q(allow_to_share=True, is_finalized=True))


    # Can voting start yet? Send user a reminder email?

    # Show number of votes remaining

    # Show name of user over their image

    return HttpResponse('Show terms here, with voting')


@csrf_exempt
@xframe_options_exempt
def keyterm_startpage(request):
    if request.method != 'POST' and (len(request.GET.keys())==0):
        return HttpResponse("You have reached the KeyTerms LTI component.")

    person_or_error, course, pr = starting_point(request)

    if course:
        if isinstance(pr, str) and isinstance(course, Course):
            #TODO: return admin_create_keyterm(request)
            return HttpResponse('<b>Create a KeyTerm first.</b> ' + pr)

    if not(isinstance(person_or_error, Person)):
        return person_or_error      # Error path if student does not exist

    learner = person_or_error
    logger.debug('Learner entering [pr={0}]: {1}'.format(pr.title, learner))


    create_hit(request, item=learner, event='login', user=learner,)

    task = KeyTerm_Task.objects.filter(resource_link_page_id=pr.LTI_id)
    terms_per_page = KeyTerm_Definition.objects.filter(keyterm_required=task)




    if terms_per_page.filter(person=learner, is_finalized=True).count() == 0:
        # If no keyterm (for this student) and (for this page), then they must
        # create one first.
        return resume_or_fill_in_keyterm(request, terms_per_page, learner)

    else:
        # If a keyterm for this student, for this page, exists, then show the
        # keyterms from student and their co-learners.
        return show_vote_keyterms(request, terms_per_page, learner)





    return HttpResponse(out)



