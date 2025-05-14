from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Vista de menú principal de la app core
    path('menu/', views.eleccion_menu, name='eleccion_menu'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('corregir/', views.corregir_ejercicio_carga_view, name='corregir_ejercicios_lista'),
    path('correccion-ejercicio-paso2/', views.mostrar_paso2_correccion_view, name='vista_paso2_correccion'),
    path('corregir-ejercicio/procesar-paso1/', views.procesar_carga_y_redirigir_a_paso2_view, name='procesar_carga_paso1'), # <--- ¡Mira este 'name'!
    path('corregir-ejercicio/paso2/', views.mostrar_paso2_correccion_view, name='vista_mostrar_paso2_correccion'),


]
