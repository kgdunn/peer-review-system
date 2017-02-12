from django.contrib import admin

from .models import Person, Group, Course, Rubric, PR_process, Submission

admin.site.register(Person)
admin.site.register(Group)
admin.site.register(Course)
admin.site.register(Rubric)
admin.site.register(PR_process)
admin.site.register(Submission)
