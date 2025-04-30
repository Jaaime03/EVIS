# core/serializers.py
from rest_framework import serializers
from .models import Examen, EnunciadoEjercicio, EjercicioAlumno, Error, AlumnoErrorEjercicio, Alumno

class ExamenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Examen
        fields = ['id_examen', 'fecha_realizacion', 'asignatura', 'convocatoria']

class EnunciadoEjercicioSerializer(serializers.ModelSerializer):
    examen = ExamenSerializer() 

    class Meta:
        model = EnunciadoEjercicio
        fields = ['id_enun_ejercicio', 'puntuacion_ejercicio', 'enunciado_ejerc', 'estructura_tablas', 'nombre_ejercicio', 'examen']

class EjercicioAlumnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EjercicioAlumno
        fields = ['id_ejercicio_alum', 'enunciado', 'ocr_imag_to_text', 'correcto_ocr', 'calif_profesor_solo']

class ErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Error
        fields = ['id_error', 'descripcion', 'penalizacion_llm', 'penalizacion_prof']

class AlumnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumno
        fields = ['id_alumno', 'nombre', 'apellidos', 'matricula', 'email', 'dni']

class AlumnoErrorEjercicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlumnoErrorEjercicio
        fields = ['alumno', 'error', 'ejercicio_alumno', 'situacion']
