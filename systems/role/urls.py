from django.urls import path
from systems.role import views

urlpatterns = [
    path("page", views.get_role_page),
    path("detail", views.get_role_detail),
    path("create", views.create_role),
    path("list", views.get_role_list),
    path("authorize", views.role_authorize),
    path("update/<int:role_id>", views.update_role),
    path("<int:role_id>", views.delete_role),
]
