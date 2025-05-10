from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Vista de menú principal de la app core
    path('menu/', views.eleccion_menu, name='eleccion_menu'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),

]
