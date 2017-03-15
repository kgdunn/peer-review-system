from django.contrib import admin

from .models import Person, Course, PR_process, PRPhase, Submission
from .models import SubmissionPhase, SelfEvaluationPhase
from .models import PeerEvaluationPhase, GradeReportPhase, FeedbackPhase
from .models import GradeComponent
from .models import RItemActual, RItemTemplate
from .models import ROptionActual, ROptionTemplate
from .models import RubricActual, RubricTemplate

class PersonAdmin(admin.ModelAdmin):
    list_display = ("display_name", "email", "is_active", "user_ID", "role")

class PR_processAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "uses_groups", "LTI_system", "LTI_id")


class PRPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "is_active", "start_dt", "end_dt")
    ordering = ['pr', 'order']
    list_filter = ['pr']

class SubmissionPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "start_dt", "end_dt", "is_active",
                    "max_file_upload_size_MB",
                    "accepted_file_types_comma_separated")

class SelfEvaluationPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "start_dt", "end_dt", "is_active")

class PeerEvaluationPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "start_dt", "end_dt", "is_active")

class FeedbackPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "start_dt", "end_dt", "is_active")

class GradeReportPhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "pr", "order", "start_dt", "end_dt", "is_active")

class GradeComponentAdmin(admin.ModelAdmin):
    list_display = ("pr", "phase", "order", "explanation", "weight", "extra_detail")
    ordering = ['pr', 'order', ]


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("submitted_by", "status", "is_valid", "file_upload",
                    "submitted_file_name", "group_submitted",
                    "number_reviews_assigned",
                    "number_reviews_completed", "datetime_submitted")

class RItemTemplateAdmin(admin.ModelAdmin):
    list_display = ("r_template", "order", "max_score", "option_type",
                    "criterion",)
    ordering = ['-r_template', 'order']
    list_filter = ['r_template']

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
    ordering = ['rubric_item', 'order']

    list_filter = ['rubric_item__r_template',
                   'rubric_item__r_template__pr_process', ]

admin.site.register(Person, PersonAdmin)
admin.site.register(Course)
admin.site.register(PR_process, PR_processAdmin)
admin.site.register(Submission, SubmissionAdmin)

admin.site.register(PRPhase, PRPhaseAdmin)
admin.site.register(SubmissionPhase, SubmissionPhaseAdmin)
admin.site.register(SelfEvaluationPhase, SelfEvaluationPhaseAdmin)
admin.site.register(PeerEvaluationPhase, PeerEvaluationPhaseAdmin)
admin.site.register(FeedbackPhase, FeedbackPhaseAdmin)
admin.site.register(GradeReportPhase, GradeReportPhaseAdmin)

admin.site.register(GradeComponent, GradeComponentAdmin)

admin.site.register(RItemActual, RItemActualAdmin)
admin.site.register(RItemTemplate, RItemTemplateAdmin)
admin.site.register(ROptionActual, ROptionActualAdmin)
admin.site.register(ROptionTemplate, ROptionTemplateAdmin)
admin.site.register(RubricActual, RubricActualAdmin)
admin.site.register(RubricTemplate)
