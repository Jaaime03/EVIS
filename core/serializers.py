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

class ImagenOCRSerializer(serializers.ModelSerializer):
    class Meta:
        model = EjercicioAlumno
        fields = ['id_ejercicio_alum', 'url_foto_ejerc', 'ocr_imag_to_text']

class ErrorDetalleSerializer(serializers.Serializer):
    id_error = serializers.IntegerField(source='error.id_error')
    descripcion = serializers.CharField(source='error.descripcion')
    situacion = serializers.CharField()
    penalizacion_llm = serializers.FloatField(source='error.penalizacion_llm')
    penalizacion_prof = serializers.FloatField(source='error.penalizacion_prof')

class ResultadoAlumnoSerializer(serializers.Serializer):
    id_ejercicio = serializers.IntegerField(source='id_ejercicio_alum')
    id_alumno = serializers.CharField(source='alumno.id_alumno')
    texto_ocr = serializers.CharField(source='ocr_imag_to_text')
    puntuacion_profesor = serializers.FloatField(source='calif_profesor_solo')
    errores = serializers.SerializerMethodField()
    puntuacion_llm = serializers.SerializerMethodField()
    puntuacion_llmprofesor = serializers.SerializerMethodField()

    def get_errores(self, obj):
        errores = AlumnoErrorEjercicio.objects.filter(ejercicio_alumno=obj)
        return ErrorDetalleSerializer(errores, many=True).data

    def get_puntuacion_llm(self, obj):
        errores = AlumnoErrorEjercicio.objects.filter(ejercicio_alumno=obj)
        penal_llm = sum(e.error.penalizacion_llm for e in errores)
        return max(obj.enunciado.puntuacion_ejercicio - penal_llm, 0.0)

    def get_puntuacion_llmprofesor(self, obj):
        errores = AlumnoErrorEjercicio.objects.filter(ejercicio_alumno=obj)
        penal_prof = sum(e.error.penalizacion_prof for e in errores)
        return max(obj.enunciado.puntuacion_ejercicio - penal_prof, 0.0)

