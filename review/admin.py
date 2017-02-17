from django.contrib import admin

from .models import Person, Group, Course, Submission #PR_process

from .models import RItemActual, RItemTemplate
from .models import ROptionActual, ROptionTemplate
from .models import RubricActual, RubricTemplate


admin.site.register(Person)
admin.site.register(Group)
admin.site.register(Course)
#admin.site.register(PR_process)
admin.site.register(Submission)

admin.site.register(RItemActual)
admin.site.register(RItemTemplate)
admin.site.register(ROptionActual)
admin.site.register(ROptionTemplate)
admin.site.register(RubricActual)
admin.site.register(RubricTemplate)
