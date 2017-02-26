from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.start_groups, name='start_groups'),
]