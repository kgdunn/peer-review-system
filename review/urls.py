from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^review/(?P<ractual_code>.+)/$',
        views.review,
        name='review'),

    url(r'^manual_create_uploads/$', views.manual_create_uploads,
        name='manual_create_uploads'),

    url(r'^submit-peer-review-feedback/(?P<ractual_code>.+)$',
        views.submit_peer_review_feedback,
        name='submit_peer_review_feedback'),

    url(r'^reset-counts/$', views.reset_counts, name='reset_counts'),
]