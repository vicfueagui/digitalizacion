from django.urls import path

from . import views

urlpatterns = [
    path("", views.batch_list, name="batch_list"),
    path("nuevo/", views.batch_create, name="batch_create"),
    path("<int:pk>/", views.batch_detail, name="batch_detail"),
    path("<int:pk>/importar-fuente/", views.batch_import_source, name="batch_import_source"),
    path(
        "<int:pk>/asociar-fuente-existente/",
        views.batch_attach_existing_source,
        name="batch_attach_existing_source",
    ),
    path("<int:pk>/crear-expedientes/", views.batch_materialize, name="batch_materialize"),
    path("<int:pk>/agregar-expediente/", views.batch_add_record, name="batch_add_record"),
    path("<int:pk>/asignar/", views.batch_assign, name="batch_assign"),
]
