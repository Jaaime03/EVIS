from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import SubirEjercicioView, ErrorInformacionView, ActualizarPenalizacionProfView, ListaImagenesYTextosOCR, CorreccionOCRView, ListaResultadosPorEjercicio, AnadirNuevoErrorView, ActualizarCalificacionProfesorView, ActualizarSituacionErrorView
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# Routers
router = DefaultRouter()
router.register(r'examenes', views.ExamenViewSet)
router.register(r'enunciados', views.EnunciadoEjercicioViewSet)
router.register(r'ejercicios-alumno', views.EjercicioAlumnoViewSet)
router.register(r'errores', views.ErrorViewSet)
router.register(r'alumnos', views.AlumnoViewSet)
router.register(r'alumno-errores', views.AlumnoErrorEjercicioViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),

    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Custom endpoint
    path('crear-ejercicio/', SubirEjercicioView.as_view(), name='crear-ejercicio'),
    path('errores-informacion/', ErrorInformacionView.as_view(), name='errores-informacion'),
    path('errores/<int:pk>/actualizar-penalizacion-prof/', ActualizarPenalizacionProfView.as_view(), name='actualizar-penalizacion-prof'),
    path('imagenes-ocr/', ListaImagenesYTextosOCR.as_view(), name='lista-imagenes-ocr'),
    path('ejercicio-alumno/<int:pk>/correccion-ocr/', CorreccionOCRView.as_view(), name='correccion-ocr'),
    path('resultados-ejercicio/<int:id_enunciado>/', ListaResultadosPorEjercicio.as_view(), name='resultados-ejercicio'),
    path('anadir-error/', AnadirNuevoErrorView.as_view(), name='anadir-error'),
    path('actualizar-calificacion/<int:pk>/', ActualizarCalificacionProfesorView.as_view(), name='actualizar-calificacion'),
    path('actualizar-situacion/<int:pk>/', ActualizarSituacionErrorView.as_view(), name='actualizar-situacion'),

    # Vista de menú principal de la app core
    path('menu/', views.eleccion_menu, name='eleccion_menu'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('corregir/', views.corregir_ejercicio_carga_view, name='corregir_ejercicios_lista'),
    path('corregir-ejercicio/procesar-paso1/', views.procesar_carga_y_redirigir_a_paso2_view, name='procesar_carga_paso1'), # <--- ¡Mira este 'name'!
    path('corregir-ejercicio/<int:id_enunciado_ejercicio>/paso2/', views.mostrar_paso2_correccion_view, name='vista_mostrar_paso2_correccion'),
    path('corregir-ejercicio/paso3-ocr/', views.mostrar_paso3_validacion_ocr_view, name='vista_mostrar_paso3_ocr'),
    path('corregir-ejercicio/paso4-final/', views.mostrar_paso4_correccion_final_view, name='vista_mostrar_paso4_final'),
    path('historial-correcciones/', views.mostrar_historial_correcciones_view, name='vista_historial_correcciones'),
    path('actualizar-penalizaciones-profesor/', views.ActualizarPenalizacionesProfesorView.as_view(), name='actualizar_penalizaciones_profesor'), # <--- NUEVA URL

]
