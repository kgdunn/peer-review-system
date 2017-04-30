from django.contrib import admin

from .models import GradeBook, GradeCategory, GradeItem, LearnerGrade

class GradeBookAdmin(admin.ModelAdmin):
    list_display = ("course", "passing_value", "max_score",)

class GradeCategoryAdmin(admin.ModelAdmin):
    list_display = ("gradebook", "display_name", "order", "max_score", "weight")
    ordering = ['order',]

class GradeItemAdmin(admin.ModelAdmin):
    list_display = ("category", "display_name", "order", "max_score", "link",
                    "weight")
    ordering = ['order',]

class LearnerGradeAdmin(admin.ModelAdmin):
    list_display = ("gitem", "learner", "value")
    ordering = ['learner', 'gitem']
    list_filter = ['learner']
    list_max_show_all = 1000
    list_per_page = 1000



admin.site.register(GradeBook, GradeBookAdmin)
admin.site.register(GradeCategory, GradeCategoryAdmin)
admin.site.register(GradeItem, GradeItemAdmin)
admin.site.register(LearnerGrade, LearnerGradeAdmin)





