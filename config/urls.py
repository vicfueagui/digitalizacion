from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

admin.site.site_header = "Administración · Digitalización SEGEY"
admin.site.site_title = "Digitalización SEGEY"
admin.site.index_title = "Configuración y catálogos"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("acceso/", auth_views.LoginView.as_view(), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("apps.core.urls")),
    path("lotes/", include("apps.batches.urls")),
    path("expedientes/", include("apps.records.urls")),
    path("digitalizacion/", include("apps.digitization.urls")),
    path("revision/", include("apps.quality.urls")),
    path("reportes/", include("apps.reports.urls")),
]
