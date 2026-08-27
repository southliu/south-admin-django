from django.urls import path
from systems.dashboard import views

urlpatterns = [
    path("partner", views.partner_list),
    path("games", views.game_list),
]
