from django.contrib import admin

from .models import KeyTerm_Definition, KeyTerm_Task, Thumbs


class KeyTerm_DefinitionAdmin(admin.ModelAdmin):
    list_display = ("person", "last_edited", "definition_text",
                    "allow_to_share", "is_finalized")
admin.site.register(KeyTerm_Definition, KeyTerm_DefinitionAdmin)



class KeyTerm_TaskAdmin(admin.ModelAdmin):
    list_display = ("keyterm_text", "deadline_for_voting", "max_thumbs",
                    "min_submissions_before_voting", "resource_link_page_id", )
admin.site.register(KeyTerm_Task, KeyTerm_TaskAdmin)



class ThumbsAdmin(admin.ModelAdmin):
    list_display = ("keyterm_definition", "last_edited", "awarded", "voter", )
admin.site.register(Thumbs, ThumbsAdmin)

