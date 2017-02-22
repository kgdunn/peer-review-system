from django.contrib import admin

from .models import Person, Group, Course, Submission, PR_process

from .models import RItemActual, RItemTemplate
from .models import ROptionActual, ROptionTemplate
from .models import RubricActual, RubricTemplate

class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "is_active", "user_ID", "role")

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("submitted_by", "status", "is_valid", "file_upload",
                    "submitted_file_name", "number_reviews_assigned",
                    "number_reviews_completed", "datetime_submitted")

class RItemActualAdmin(admin.ModelAdmin):
    list_display = ("ritem_template", "submitted", "comment",
                    "created", "modified",)

class RubricActualAdmin(admin.ModelAdmin):
    list_display = ("created", "modified", "submitted", "graded_by",
                    "submission", "unique_code",)



admin.site.register(Person, PersonAdmin)
admin.site.register(Group)
admin.site.register(Course)
admin.site.register(PR_process)
admin.site.register(Submission, SubmissionAdmin)

admin.site.register(RItemActual, RItemActualAdmin)
admin.site.register(RItemTemplate)
admin.site.register(ROptionActual)
admin.site.register(ROptionTemplate)
admin.site.register(RubricActual, RubricActualAdmin)
admin.site.register(RubricTemplate)