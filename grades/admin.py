from django.contrib import admin

from .models import GradeBook, GradeCategory, GradeItem, LearnerGrade

class GradeBookAdmin(admin.ModelAdmin):
    list_display = ("course", "passing_value", "max_score",)

class GradeCategoryAdmin(admin.ModelAdmin):
    list_display = ("gradebook", "order", "max_score", "weight")

class GradeItemAdmin(admin.ModelAdmin):
    list_display = ("category", "order", "max_score", "link", "weight")

class LearnerGradeAdmin(admin.ModelAdmin):
    list_display = ("gitem", "learner", "value")


admin.site.register(GradeBook, GradeBookAdmin)
admin.site.register(GradeCategory, GradeCategoryAdmin)
admin.site.register(GradeItem, GradeItemAdmin)
admin.site.register(LearnerGrade, LearnerGradeAdmin)





