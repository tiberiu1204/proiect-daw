from django.urls import path
from . import views

urlpatterns = [
    path('produse/', views.filtru_produse, name='filtru_produse'),
    path('contact/', views.contact_view, name='contact'),
    path('adauga_produs/', views.adauga_produs, name='adauga_produs'),
]
