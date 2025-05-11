from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import SubirEjercicioView, ErrorInformacionView, ActualizarPenalizacionProfView, ListaImagenesYTextosOCR, CorreccionOCRView, ListaResultadosPorEjercicio, AnadirNuevoErrorView, ActualizarCalificacionProfesorView, ActualizarSituacionErrorView

# Routers
router = DefaultRouter()
router.register(r'examenes', views.ExamenViewSet)
router.register(r'enunciados', views.EnunciadoEjercicioViewSet)
router.register(r'ejercicios-alumno', views.EjercicioAlumnoViewSet)
router.register(r'errores', views.ErrorViewSet)
router.register(r'alumnos', views.AlumnoViewSet)
router.register(r'alumno-errores', views.AlumnoErrorEjercicioViewSet)

# URL patterns
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
]
