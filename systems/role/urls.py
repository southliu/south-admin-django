from django.urls import path

from . import views

urlpatterns = [
    path('page', views.page, name='page'),
    path('list', views.list_roles, name='list'),
    path('create', views.create, name='create'),
    path('<int:role_id>', views.delete, name='delete'),
    path('update/<int:role_id>', views.update, name='update'),
    path('detail', views.detail, name='detail'),
    path('authorize', views.authorize, name='authorize'),
    path('authorize/save', views.save_authorize, name='save_authorize'),
]
