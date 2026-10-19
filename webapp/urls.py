from django.urls import path
from . import views
from . import desk_views
from . import desk_import

urlpatterns = [
    path('expedientes/<int:work>/codificacion/importar/preparar/', desk_import.stage, name='desk_import_stage'),
    path('expedientes/<int:work>/codificacion/importar/confirmar/', desk_import.confirm, name='desk_import_confirm'),
    path('expedientes/<int:work>/codificacion/importar/cancelar/', desk_import.cancel, name='desk_import_cancel'),
    path('preferencias/mesa/', desk_views.preference, name='desk_preferences'),
    path('expedientes/<int:work>/codificacion/', desk_views.station, name='coding_desk'),
    path('expedientes/<int:work>/codificacion/accion/', desk_views.execute, name='desk_action'),
    path('expedientes/<int:work>/codificacion/plan-paginas/', desk_views.page_plan, name='desk_page_plan'),
    path('expedientes/<int:work>/codificacion/ajuste/<int:ident>/<int:page>/', desk_views.edit_preview, name='desk_edit_preview'),
    path('expedientes/<int:work>/codificacion/imagen/<int:ident>/<int:page>/', desk_views.preview, name='desk_preview'),
    path('expedientes/<int:work>/codificacion/historial/<int:ident>/<int:page>/', desk_views.history, name='desk_history'),
    path('acceso/', views.access, name='access'), path('salir/', views.exit_session, name='logout'),
    path('', views.home, name='home'), path('expedientes/', views.works, name='works'),
    path('expedientes/<int:work>/', views.expediente, name='expediente'),
    path('expedientes/<int:work>/conteo/', views.count_desk, name='count_desk'),
    path('expedientes/<int:work>/accion/<str:action>/', views.action, name='work_action'),
    path('expedientes/<int:work>/imagen/<int:file_id>/<int:page>/', views.preview_image, name='image'),
    path('accion/<str:action>/', views.action, name='action'), path('folios/', views.folios, name='folios'),
    path('kanban/', views.kanban, name='kanban'), path('indicadores/', views.indicators, name='indicators'),
    path('ayuda/', views.help_page, name='help'), path('administracion/', views.maintenance, name='maintenance'),
    path('expedientes/<int:work>/entrega/<str:delivery>/', views.delivery_view, name='delivery'),
    path('expedientes/<int:work>/entrega/<str:delivery>/imagen/<int:file_id>/<int:page>/', views.delivery_image, name='delivery_image'),
    path('importar-lista/', views.import_list, name='import_list'), path('importar-lista/vista-previa/', views.import_preview, name='import_preview'),
]
