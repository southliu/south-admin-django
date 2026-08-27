from django.contrib import admin
from django.urls import path, include

from systems.dashboard import views as dashboard_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("system/user/", include("systems.user.urls")),
    path("system/role/", include("systems.role.urls")),
    path("system/menu/", include("systems.menu.urls")),
    path("system/permission/", include("systems.permission.urls")),
    path("system/log/", include("systems.log.urls")),
    # 仪表盘及下拉演示数据（写死）
    path("dashboard", dashboard_views.dashboard_trends),
    path("platform/", include("systems.dashboard.urls")),
    path("authority/common/", include("systems.dashboard.urls")),
]
