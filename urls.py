from django.conf.urls import url

from . import views

app_name = 'pisces'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^authenticate/$', views.authenticate, name='authenticate'),
]