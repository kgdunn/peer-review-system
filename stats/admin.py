from django.contrib import admin
from .models import Timer
class TimerAdmin(admin.ModelAdmin):
    list_display =('datetime', 'user', 'event', 'item_pk',
                   'item_name', 'other_info', 'referrer')
    list_per_page = 5000


admin.site.register(Timer, TimerAdmin)

