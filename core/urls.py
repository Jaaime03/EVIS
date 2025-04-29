from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EjercicioViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'ejercicios', EjercicioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns += [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]