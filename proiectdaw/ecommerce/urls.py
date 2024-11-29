from django.urls import path
from .views import register_view, login_view, logout_view, profile_view, change_password_view, homepage, confirmation_view, email_confirmat
from . import views

urlpatterns = [
    path('', views.homepage, name='home'),
    path('produse/', views.filtru_produse, name='filtru_produse'),
    path('contact/', views.contact_view, name='contact'),
    path('adauga-produs/', views.adauga_produs, name='adauga_produs'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('change-password/', change_password_view, name='change_password'),
    path('confirmation-sent/', confirmation_view, name='confirmation_view'),
    path('confirma-mail/<str:cod>/', email_confirmat, name='email_confirmat'),
]
