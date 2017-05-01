from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^import_grades$',
        views.import_edx_gradebook,
        name='import_edx_gradebook'),

    url(r'^display-grade/(?P<user_ID>.+)/(?P<course>.+)$',
        views.display_grade,
        name='display_grade')
]