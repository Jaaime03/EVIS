from django.contrib import admin

from .models import Examen, EnunciadoEjercicio, EjercicioAlumno, Error, Alumno, AlumnoErrorEjercicio

admin.site.register(Examen)
admin.site.register(EnunciadoEjercicio)
admin.site.register(EjercicioAlumno)
admin.site.register(Error)
admin.site.register(Alumno)
admin.site.register(AlumnoErrorEjercicio)
