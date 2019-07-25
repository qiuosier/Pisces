from django.conf.urls import url

from . import views

app_name = 'pisces'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^authenticate/$', views.authenticate, name='authenticate'),
    url(r'^home/$', views.home, name='home'),
    url(r'^observations/$', views.observations, name='observations'),
]