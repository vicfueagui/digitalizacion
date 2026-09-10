from django.urls import path

from . import views

urlpatterns = [
    path("", views.review_queue, name="review_queue"),
    path("<int:pk>/", views.review_detail, name="review_detail"),
]
