from django.urls import path

from . import views

urlpatterns = [
    path('list', views.list, name='list'),
    path('page', views.page, name='page'),
    path('create', views.create, name='create'),
    path('<int:menu_id>', views.delete, name='delete'),
    path('update/<int:menu_id>', views.update, name='update'),
    path('detail', views.detail, name='detail'),
    path('changeState', views.change_state, name='change_state'),
    path('tree', views.tree, name='tree'),
    path('authorize/save', views.save_authorize, name='save_authorize'),
]
