from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.start_groups, name='start_groups'),
    url(r'^import_classlist$', views.import_classlist, name='import_classlist')
]