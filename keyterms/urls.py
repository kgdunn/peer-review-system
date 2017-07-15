from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.keyterm_startpage, name='start_keyterms'),


]