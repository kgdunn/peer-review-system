from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^review/(?P<ractual_code>.+)/$',
        views.review,
        name='review'),

    url(r'^manual_create_uploads/$', views.manual_create_uploads,
        name='manual_create_uploads'),

    url(r'^submit-feedback/(?P<ractual_code>.+)$',
        views.submit_feedback,
        name='submit_feedback')
]

"""
Internal URL structure:

/learner/__<stage>__/




<form action="upload.php" method="post" enctype="multipart/form-data">
    Select image to upload:
    <input type="file" name="fileToUpload" id="fileToUpload">
    <input type="submit" value="Upload Image" name="submit">
</form>


"""