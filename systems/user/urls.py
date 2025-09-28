from django.urls import path

from . import views

app_name = 'user'

urlpatterns = [
    path('login', views.login, name='login'),
    path('refreshPermissions', views.refresh_permissions, name='refresh_permissions'),
    path('page', views.page, name='page'),
    path('list', views.list_users, name='list'),
    path('detail', views.detail, name='detail'),
    path('create', views.create, name='create'),
    path('update/<int:user_id>', views.update, name='update'),
    path('delete/<int:user_id>', views.delete, name='delete'),
    path('updatePassword', views.update_password, name='update_password'),
    path('authorize', views.authorize, name='authorize'),
    path('authorize/save', views.save_user_authorization, name='save_user_authorization'),
]
