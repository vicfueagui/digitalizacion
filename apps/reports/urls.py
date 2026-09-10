from django.urls import path

from . import views

urlpatterns = [path("", views.operational_report, name="operational_report")]
