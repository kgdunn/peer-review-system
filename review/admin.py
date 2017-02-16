from django.contrib import admin

from .models import Person, Group, Course, PR_process, Submission
from .models import QSet, QTemplate, QActual

admin.site.register(Person)
admin.site.register(Group)
admin.site.register(Course)
admin.site.register(PR_process)
admin.site.register(Submission)

admin.site.register(QSet)
admin.site.register(QTemplate)
admin.site.register(QActual)
