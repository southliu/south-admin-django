from django.urls import path

from . import views

urlpatterns = [
    path('login', views.login, name='login'),
    # path('refresh-permissions', views.refresh_permissions, name='refresh-permissions'),
    # path('page', views.get_page, name='user'),
    # path('update-password', views.UpdatePasswordView.as_view(), name='update-password'),
]