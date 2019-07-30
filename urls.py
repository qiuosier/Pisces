from django.conf.urls import url

from . import views

app_name = 'pisces'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^authenticate/$', views.authenticate, name='authenticate'),
    url(r'^home/$', views.home, name='home'),
    url(r'^observations/(?P<category>[A-Za-z]+)/$', views.view_observations, name='observations'),
    url(r'^observations/Laboratory/(?P<code>[A-Za-z0-9\-]+)/$', views.view_laboratory, name='laboratory'),
    url(r'^logout/$', views.logout, name='logout'),
]
