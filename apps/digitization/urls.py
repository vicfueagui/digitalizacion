from django.urls import path

from . import views

urlpatterns = [
    path("expediente/<int:record_pk>/documento/", views.document_add, name="document_add"),
    path("expediente/<int:record_pk>/tiff/", views.asset_add, name="asset_add"),
    path("expediente/<int:record_pk>/inventariar/", views.inventory_record, name="inventory_record"),
    path("lote/<int:batch_pk>/importar-bat/", views.bat_import, name="bat_import"),
]
