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
    path('corregir-ejercicio/paso3-ocr/', views.mostrar_paso3_validacion_ocr_view, name='vista_mostrar_paso3_ocr'),
    path('corregir-ejercicio/paso4-final/', views.mostrar_paso4_correccion_final_view, name='vista_mostrar_paso4_final'),
    path('historial-correcciones/', views.mostrar_historial_correcciones_view, name='vista_historial_correcciones'),

]
