from django.urls import path

from . import views

app_name = 'article'

urlpatterns = [
    path('page', views.page, name='page'),
    path('list', views.list_articles, name='list'),
    path('detail', views.detail, name='detail'),
    path('create', views.create, name='create'),
    path('update/<int:article_id>', views.update, name='update'),
    path('delete/<int:article_id>', views.delete, name='delete'),
]