"""
peer URL Configuration

"""
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include('review.urls')),
    url(r'groups/', include('groups.urls'))
]

