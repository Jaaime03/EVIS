# core/serializers.py

from rest_framework import serializers
from .models import Ejercicio, Alumno, EjercicioAlumno

class AlumnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumno
        fields = ['id', 'username', 'email', 'first_name', 'last_name']