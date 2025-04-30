from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'examenes', views.ExamenViewSet)
router.register(r'enunciados', views.EnunciadoEjercicioViewSet)
router.register(r'ejercicios-alumno', views.EjercicioAlumnoViewSet)
router.register(r'errores', views.ErrorViewSet)
router.register(r'alumnos', views.AlumnoViewSet)
router.register(r'alumno-errores', views.AlumnoErrorEjercicioViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]

urlpatterns += [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns += [
    path('crear_examen/', views.crear_examen, name='crear_examen'),
    path('crear_enunciado_ejercicio/', views.crear_enunciado_ejercicio, name='crear_enunciado_ejercicio'),
    path('subir_imagenes/', views.subir_imagenes_ejercicio, name='subir_imagenes'),
    path('procesar-ocr/', views.procesar_ocr_api, name='procesar_ocr'),
    path('procesar-correccion/', views.procesar_correccion_api, name='procesar_correccion'),
]