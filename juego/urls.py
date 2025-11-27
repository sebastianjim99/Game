from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),          # formulario inicial
    path("jugar/", views.jugar, name="jugar"),  # vista del juego
    path("responder/", views.responder, name="responder"),  # procesa la respuesta
    path("ranking/", views.ranking, name="ranking"),  # ← NUEVO

    # NUEVAS rutas para ayudas
    path("ayuda/5050/", views.ayuda_5050, name="ayuda_5050"),
    path("ayuda/publico/", views.ayuda_publico, name="ayuda_publico"),
    path("ayuda/amigo/", views.ayuda_amigo, name="ayuda_amigo"),
    path("ayuda/cambiar/", views.ayuda_cambiar, name="ayuda_cambiar"),
]