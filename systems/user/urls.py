from django.urls import path

from . import views

urlpatterns = [
    path('login', views.login, name='login'),
    path('refresh-permissions', views.refresh_permissions, name='refresh-permissions'),
    path('page', views.page, name='page'),
    path('list', views.list_users, name='list'),
    path('detail', views.detail, name='detail'),
    path('create', views.create, name='create'),
    path('update/<int:user_id>', views.update, name='update'),
    path('delete/<int:user_id>', views.delete, name='delete'),
    # path('update-password', views.UpdatePasswordView.as_view(), name='update-password'),
]
