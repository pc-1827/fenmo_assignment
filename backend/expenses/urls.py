from django.urls import re_path
from . import views, health

urlpatterns = [
    re_path(r'^expenses/?$', views.expenses_collection, name='expenses_collection'),
    re_path(r'^health/?$', health.health_check, name='health_check'),
]
