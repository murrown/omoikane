from django.conf.urls import url
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^get/lists$', views.lists),
    url(r'^post/due$', views.due),
    url(r'^post/success$', views.success),
    url(r'^post/failure$', views.failure),
]
