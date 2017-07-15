from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include('review.urls')),
    url(r'groups/', include('groups.urls')),
    url(r'grades/', include('grades.urls')),
    url(r'keyterms/', include('keyterms.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


