from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from core.views import login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('login/', include('login.urls')), 
    path('', include('core.urls')), 
]

# Solo en desarrollo: servir archivos estáticos
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
