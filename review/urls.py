from django.conf.urls import url

from . import views

urlpatterns = [
    #url(r'', views.index, name='index'),
    url(r'^$', views.index, name='index'),
    url(r'^success/$', views.success, name='success'),
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