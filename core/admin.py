from django.contrib import admin

from .models import Examen, EnunciadoEjercicio, EjercicioAlumno, Error, Alumno, AlumnoErrorEjercicio

admin.site.register(Examen)
admin.site.register(EnunciadoEjercicio)
admin.site.register(EjercicioAlumno)
admin.site.register(Error)
admin.site.register(Alumno)
from django.contrib import admin
from django.contrib.auth.models import User
admin.site.register(AlumnoErrorEjercicio)
class CustomUserAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Solo permitir que el superuser añada usuarios
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Puedes personalizar si quieres que solo el superuser también edite
        return request.user.is_superuser

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)