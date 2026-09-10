from django.urls import path

from . import views

urlpatterns = [
    path("", views.record_list, name="record_list"),
    path("<int:pk>/", views.record_detail, name="record_detail"),
    path("<int:pk>/asignar/", views.record_assign, name="record_assign"),
    path("<int:pk>/aceptar/", views.record_accept, name="record_accept"),
    path("<int:pk>/iniciar/", views.record_start, name="record_start"),
    path("<int:pk>/conteo-fisico/", views.record_add_physical_count, name="record_add_physical_count"),
    path("<int:pk>/incidencia/", views.record_add_incident, name="record_add_incident"),
    path("<int:pk>/enviar-revision/", views.record_submit, name="record_submit"),
    path("<int:pk>/enviar-correccion/", views.record_corrected, name="record_corrected"),
    path("<int:pk>/cerrar/", views.record_close, name="record_close"),
    path("incidencia/<int:pk>/resolver/", views.incident_resolve, name="incident_resolve"),
]
