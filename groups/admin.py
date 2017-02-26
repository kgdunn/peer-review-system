from django.contrib import admin

from .models import Group, Group_Formation_Process, Enrolled

class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "capacity", )

class Group_Formation_ProcessAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "dt_groups_open_up",
                    "dt_selfenroll_starts", "dt_group_selection_stops",
                    "allow_unenroll", "show_fellows", "show_description",
                    "random_add_unenrolled_after_cutoff")

class EnrolledAdmin(admin.ModelAdmin):
    list_display = ("person", "group", "is_enrolled", "created", "modified")


admin.site.register(Group, GroupAdmin)
admin.site.register(Group_Formation_Process, Group_Formation_ProcessAdmin)
admin.site.register(Enrolled, EnrolledAdmin)


