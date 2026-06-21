from django.urls import path
from systems.menu import views

urlpatterns = [
    path("list", views.get_menu_list),
    path("page", views.get_menu_page),
    path("detail", views.get_menu_detail),
    path("create", views.create_menu),
    path("batchDelete", views.batch_delete_menu),
    path("changeState", views.change_menu_state),
    path("update/<int:menu_id>", views.update_menu),
    path("<int:menu_id>", views.delete_menu),
]
