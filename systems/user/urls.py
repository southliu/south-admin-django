from django.urls import path
from systems.user import views

urlpatterns = [
    path("login", views.login),
    path("logout", views.logout),
    path("refreshPermissions", views.refresh_permissions),
    path("page", views.get_user_page),
    path("detail", views.get_user_detail),
    path("create", views.create_user),
    path("list", views.get_user_list),
    path("updatePassword", views.update_password),
    path("update/<int:user_id>", views.update_user),
    path("<int:user_id>", views.delete_user),
]
