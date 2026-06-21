from django.urls import path
from systems.log import views

urlpatterns = [
    path("create", views.create_log),
    path("page", views.get_log_page),
    path("batchDelete", views.batch_delete_log),
    path("<int:log_id>", views.delete_log),
]
