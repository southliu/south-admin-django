from django.urls import path

from . import views

urlpatterns = [
    path('list', views.list, name='list'),
    path('page', views.page, name='page'),
    path('create', views.create, name='create'),
    path('<int:menu_id>', views.delete, name='delete'),
    path('update/<int:menu_id>', views.update, name='update'),
    path('detail', views.detail, name='detail'),
]