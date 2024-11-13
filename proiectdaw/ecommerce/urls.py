from django.urls import path
from . import views

urlpatterns = [
    path('produse/', views.filtru_produse, name='filtru_produse'),
]
