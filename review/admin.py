from django.contrib import admin

from .models import Person, Course, PR_process
from .models import SubmissionPhase, SelfEvaluationPhase, PeerEvaluationPhase
from .models import PRPhase, FeedbackPhase, Submission
from .models import RItemActual, RItemTemplate
from .models import ROptionActual, ROptionTemplate
from .models import RubricActual, RubricTemplate

class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "is_active", "user_ID", "role")

class PR_processAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "uses_groups", "LTI_system", "LTI_id")


class PRPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "is_active", "start_dt", "end_dt")
    ordering = ['pr', 'order']

class SubmissionPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "start_dt", "end_dt",
                    "max_file_upload_size_MB",
                    "accepted_file_types_comma_separated")

class SelfEvaluationPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "start_dt", "end_dt",
                    "instructions",)

class PeerEvaluationPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "start_dt", "end_dt",
                    "instructions",)

class FeedbackPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "start_dt", "end_dt",
                    "instructions",)

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("submitted_by", "status", "is_valid", "file_upload",
                    "submitted_file_name", "group_submitted",
                    "number_reviews_assigned",
                    "number_reviews_completed", "datetime_submitted")

class RItemTemplateAdmin(admin.ModelAdmin):
    list_display = ("r_template", "order", "max_score", "option_type",
                    "criterion", "created", "modified",)
    ordering = ['-r_template', 'order']

class RItemActualAdmin(admin.ModelAdmin):
    list_display = ("ritem_template", "submitted", "comment",
                    "created", "modified",)

class RubricActualAdmin(admin.ModelAdmin):
    list_display = ("submission", "submitted", "status", "graded_by",
                    "unique_code", "created", "modified")

class ROptionActualAdmin(admin.ModelAdmin):
    list_display = ("roption_template", "ritem_actual", "submitted",
                    "comment", "created", "modified")

class ROptionTemplateAdmin(admin.ModelAdmin):
    list_display = ("rubric_item", "order", "score", "short_text",)
    ordering = ['-rubric_item', 'order']

admin.site.register(Person, PersonAdmin)
admin.site.register(Course)
admin.site.register(PR_process, PR_processAdmin)
admin.site.register(Submission, SubmissionAdmin)

admin.site.register(PRPhase, PRPhaseAdmin)
admin.site.register(SubmissionPhase, SubmissionPhaseAdmin)
admin.site.register(SelfEvaluationPhase, SelfEvaluationPhaseAdmin)
admin.site.register(PeerEvaluationPhase, PeerEvaluationPhaseAdmin)
admin.site.register(FeedbackPhase, FeedbackPhaseAdmin)

admin.site.register(RItemActual, RItemActualAdmin)
admin.site.register(RItemTemplate, RItemTemplateAdmin)
admin.site.register(ROptionActual, ROptionActualAdmin)
admin.site.register(ROptionTemplate, ROptionTemplateAdmin)
admin.site.register(RubricActual, RubricActualAdmin)
admin.site.register(RubricTemplate)
