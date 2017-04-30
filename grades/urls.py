from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^import_grades$',
        views.import_edx_gradebook,
        name='import_edx_gradebook'),
]