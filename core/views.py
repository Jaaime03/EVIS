# core/views.py
import os
import zipfile
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from core.models import Examen, EnunciadoEjercicio, EjercicioAlumno, Alumno
from core.utils.procesar_ocr import procesar_ocr
from core.utils.imagen_detectar_errores import imagen_detectar_errores
from core.utils.detectar_errores import detectar_errores
from core.pagination import ImagenOCRPagination, EjercicioAlumnoPagination
from rest_framework import viewsets
from .models import Examen, EnunciadoEjercicio, EjercicioAlumno, Error, Alumno, AlumnoErrorEjercicio
from .serializers import ExamenSerializer, EnunciadoEjercicioSerializer, EjercicioAlumnoSerializer, ErrorSerializer, AlumnoSerializer, AlumnoErrorEjercicioSerializer, ImagenOCRSerializer, ResultadoAlumnoSerializer
from django.shortcuts import get_object_or_404


# Vista para manejar Examenes
class ExamenViewSet(viewsets.ModelViewSet):
    queryset = Examen.objects.all()
    serializer_class = ExamenSerializer

# Vista para manejar Enunciados
class EnunciadoEjercicioViewSet(viewsets.ModelViewSet):
    queryset = EnunciadoEjercicio.objects.all()
    serializer_class = EnunciadoEjercicioSerializer

# Vista para manejar Ejercicios de Alumno
class EjercicioAlumnoViewSet(viewsets.ModelViewSet):
    queryset = EjercicioAlumno.objects.all()
    serializer_class = EjercicioAlumnoSerializer

# Vista para manejar Errores
class ErrorViewSet(viewsets.ModelViewSet):
    queryset = Error.objects.all()
    serializer_class = ErrorSerializer

# Vista para manejar Alumnos
class AlumnoViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer

# Vista para manejar los errores de los alumnos
class AlumnoErrorEjercicioViewSet(viewsets.ModelViewSet):
    queryset = AlumnoErrorEjercicio.objects.all()
    serializer_class = AlumnoErrorEjercicioSerializer

class SubirEjercicioView(APIView):
    def post(self, request):
        try:
            # 1. Recoger datos del formulario
            asignatura = request.data['asignatura']
            convocatoria = request.data['convocatoria']
            fecha_realizacion = request.data['fecha_realizacion']
            nombre_ejercicio = request.data['nombre_ejercicio']
            enunciado_ejerc = request.data['enunciado_ejerc']
            estructura_tablas = request.FILES['estructura_tablas']
            puntuacion = request.data['puntuacion']
            archivo_zip = request.FILES['zip']

            # 2. Crear Examen
            examen = Examen.objects.create(
                asignatura=asignatura,
                convocatoria=convocatoria,
                fecha_realizacion=fecha_realizacion
            )

            # 3. Crear EnunciadoEjercicio con imagen
            enunciado = EnunciadoEjercicio.objects.create(
                nombre_ejercicio=nombre_ejercicio,
                enunciado_ejerc=enunciado_ejerc,
                estructura_tablas=estructura_tablas,
                puntuacion_ejercicio=puntuacion,
                examen=examen
            )

            # 4. Guardar ZIP temporalmente
            zip_path = default_storage.save('tmp/fotos.zip', archivo_zip)
            zip_absoluto = os.path.join(settings.MEDIA_ROOT, zip_path)

            # 5. Crear carpeta destino
            carpeta_destino = os.path.join(settings.MEDIA_ROOT, f'ejercicios/{enunciado.id_enun_ejercicio}')
            os.makedirs(carpeta_destino, exist_ok=True)

            # 6. Extraer ZIP
            with zipfile.ZipFile(zip_absoluto, 'r') as zip_ref:
                zip_ref.extractall(carpeta_destino)

            # 7. Crear objetos EjercicioAlumno
            for nombre_archivo in os.listdir(carpeta_destino):
                if nombre_archivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                    alumno_id = os.path.splitext(nombre_archivo)[0]
                    try:
                        alumno = Alumno.objects.get(id_alumno=int(alumno_id))
                        url_foto = f"ejercicios/{enunciado.id_enun_ejercicio}/{nombre_archivo}"

                        EjercicioAlumno.objects.create(
                            enunciado=enunciado,
                            alumno=alumno,
                            url_foto_ejerc=url_foto,
                            estado='Pendiente'
                        )
                    except Alumno.DoesNotExist:
                        continue

            os.remove(zip_absoluto)

            # 8. Ejecutar OCR
            transcripciones = procesar_ocr(carpeta_destino)

            # 9. Ejecutar corrección de errores — CAMBIO AQUÍ
            imagen_detectar_errores(transcripciones, enunciado)

            return Response({'mensaje': 'Ejercicio creado y corregido correctamente'}, status=201)

        except Exception as e:
            return Response({'error': str(e)}, status=400)

class ErrorInformacionView(APIView):
    def get(self, request):
        errores = Error.objects.all()
        data = []

        for error in errores:
            count_alumnos = AlumnoErrorEjercicio.objects.filter(error=error).values('alumno').distinct().count()

            data.append({
                'id_error': error.id_error,
                'descripcion': error.descripcion,
                'num_alumnos': count_alumnos,
                'penalizacion_llm': error.penalizacion_llm,
                'penalizacion_prof': error.penalizacion_prof
            })

        return Response(data, status=200)

class ActualizarPenalizacionProfView(APIView):
    def patch(self, request, pk):
        try:
            error = Error.objects.get(pk=pk)
        except Error.DoesNotExist:
            return Response({"error": "Error no encontrado"}, status=404)

        nueva_penalizacion = request.data.get("penalizacion_prof")
        if nueva_penalizacion is None:
            return Response({"error": "Se requiere 'penalizacion_prof'"}, status=400)

        try:
            error.penalizacion_prof = float(nueva_penalizacion)
            error.save()
            return Response({"mensaje": "Penalización actualizada correctamente"}, status=200)
        except ValueError:
            return Response({"error": "Valor de penalización inválido"}, status=400)
        
class ListaImagenesYTextosOCR(ListAPIView):
    queryset = EjercicioAlumno.objects.all()
    serializer_class = ImagenOCRSerializer
    pagination_class = ImagenOCRPagination 

class CorreccionOCRView(APIView):
    def patch(self, request, pk):
        ejercicio = get_object_or_404(EjercicioAlumno, pk=pk)
        correcto_ocr = request.data.get('correcto_ocr')
        correccion_ocr_hum = request.data.get('correccion_ocr_hum', '')

        if correcto_ocr is None:
            return Response({'error': 'Se requiere el campo correcto_ocr'}, status=400)

        if not isinstance(correcto_ocr, bool):
            return Response({'error': 'El campo correcto_ocr debe ser booleano'}, status=400)

        if not correcto_ocr and not correccion_ocr_hum:
            return Response({'error': 'Si correcto_ocr es False, se debe incluir correccion_ocr_hum'}, status=400)

        ejercicio.correcto_ocr = correcto_ocr
        ejercicio.correccion_ocr_hum = correccion_ocr_hum if not correcto_ocr else ''
        ejercicio.save()

        return Response({'mensaje': 'Actualización exitosa'}, status=200)

class ListaResultadosPorEjercicio(ListAPIView):
    serializer_class = ResultadoAlumnoSerializer
    pagination_class = EjercicioAlumnoPagination

    def get_queryset(self):
        enun_id = self.kwargs.get('id_enunciado')
        return EjercicioAlumno.objects.filter(enunciado__id_enun_ejercicio=enun_id)
    

class AnadirNuevoErrorView(APIView):
    def post(self, request):
        try:
            id_alumno = request.data.get('id_alumno')
            id_ejercicio_alumno = request.data.get('id_ejercicio_alumno')
            descripcion = request.data.get('descripcion')
            penalizacion_prof = request.data.get('penalizacion_prof')

            if not all([id_alumno, id_ejercicio_alumno, descripcion, penalizacion_prof]):
                return Response({"error": "Todos los campos son requeridos"}, status=400)

            alumno = Alumno.objects.get(pk=id_alumno)
            ejercicio = EjercicioAlumno.objects.get(pk=id_ejercicio_alumno)

            # Crear el nuevo error
            nuevo_error = Error.objects.create(
                descripcion=descripcion,
                penalizacion_llm=0,
                penalizacion_prof=penalizacion_prof
            )

            # Asociar el error al alumno y ejercicio con situación 'Anadido'
            AlumnoErrorEjercicio.objects.create(
                alumno=alumno,
                error=nuevo_error,
                ejercicio_alumno=ejercicio,
                situacion='Anadido'
            )

            return Response({
                "mensaje": "Error creado y asociado correctamente",
                "id_error": nuevo_error.id_error
            }, status=201)

        except Alumno.DoesNotExist:
            return Response({"error": "Alumno no encontrado"}, status=404)
        except EjercicioAlumno.DoesNotExist:
            return Response({"error": "Ejercicio del alumno no encontrado"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class ActualizarCalificacionProfesorView(APIView):
    def patch(self, request, pk):
        ejercicio = get_object_or_404(EjercicioAlumno, pk=pk)
        nueva_calificacion = request.data.get("calif_profesor_solo")

        if nueva_calificacion is None:
            return Response({"error": "Se requiere el campo 'calif_profesor_solo'"}, status=400)

        try:
            ejercicio.calif_profesor_solo = float(nueva_calificacion)
            ejercicio.save()
            return Response({"mensaje": "Calificación actualizada correctamente"}, status=200)
        except ValueError:
            return Response({"error": "Valor de calificación inválido"}, status=400)

class ActualizarSituacionErrorView(APIView):
    def patch(self, request, pk):
        alumno_error = get_object_or_404(AlumnoErrorEjercicio, pk=pk)
        nueva_situacion = request.data.get("situacion")

        if nueva_situacion not in ['Correcto', 'Incorrecto', 'Anadido', 'Añadido']:
            return Response(
                {"error": "Situación inválida. Debe ser 'Correcto', 'Incorrecto', 'Anadido' o 'Añadido'."},
                status=400
            )

        alumno_error.situacion = nueva_situacion
        alumno_error.save()
        return Response({"mensaje": "Situación actualizada correctamente."}, status=200)
