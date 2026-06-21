from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("system/user/", include("systems.user.urls")),
    path("system/role/", include("systems.role.urls")),
    path("system/menu/", include("systems.menu.urls")),
    path("system/permission/", include("systems.permission.urls")),
    path("system/log/", include("systems.log.urls")),
]
