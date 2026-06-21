from django.urls import path
from systems.permission import views

urlpatterns = [
    path("page", views.get_permission_page),
    path("detail", views.get_permission_detail),
    path("create", views.create_permission),
    path("list", views.get_permission_list),
    path("update/<int:permission_id>", views.update_permission),
    path("<int:permission_id>", views.delete_permission),
]
