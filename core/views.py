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
from core.utils.detectar_errores import detectar_errores
from core.pagination import ImagenOCRPagination, EjercicioAlumnoPagination
from rest_framework import viewsets
from .models import Examen, EnunciadoEjercicio, EjercicioAlumno, Error, Alumno, AlumnoErrorEjercicio
from .serializers import ExamenSerializer, EnunciadoEjercicioSerializer, EjercicioAlumnoSerializer, ErrorSerializer, AlumnoSerializer, AlumnoErrorEjercicioSerializer, ImagenOCRSerializer, ResultadoAlumnoSerializer
from django.shortcuts import get_object_or_404
import datetime
from rest_framework.viewsets import ModelViewSet

from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect

from core.models import EnunciadoEjercicio, Examen

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
        print('1:Recibiendo datos de la vista de subida de ejercicios')
        try:
            # 1. Recoger datos del formulario
            asignatura = request.data['asignatura']
            convocatoria = request.data['convocatoria']
            fecha_realizacion = request.data['fecha_realizacion']
            nombre_ejercicio = request.data['nombre_ejercicio']
            archivo_enunciado = request.FILES['enunciado_ejerc']
            enunciado_ejerc = archivo_enunciado.read().decode('utf-8')
            estructura_tablas = request.FILES['estructura_tablas']
            puntuacion = request.data['puntuacion']
            archivo_zip = request.FILES['zip']

            print('2:Datos recibidos:', asignatura, convocatoria, fecha_realizacion, nombre_ejercicio, enunciado_ejerc, estructura_tablas, puntuacion)
            # 2. Crear Examen
            examen = Examen.objects.create(
                asignatura=asignatura,
                convocatoria=convocatoria,
                fecha_realizacion=fecha_realizacion
            )
            print('3:Examen creado:', examen)
            # 3. Crear EnunciadoEjercicio con imagen
            enunciado = EnunciadoEjercicio.objects.create(
                nombre_ejercicio=nombre_ejercicio,
                enunciado_ejerc=enunciado_ejerc,
                estructura_tablas=estructura_tablas,
                puntuacion_ejercicio=puntuacion,
                examen=examen
            )
            print('4:EnunciadoEjercicio creado:', enunciado)
            # 4. Guardar ZIP temporalmente
            zip_path = default_storage.save('tmp/fotos.zip', archivo_zip)
            zip_absoluto = os.path.join(settings.MEDIA_ROOT, zip_path)

            print('5:ZIP guardado en:', zip_absoluto)
            # 5. Crear carpeta destino
            carpeta_destino = os.path.join(settings.MEDIA_ROOT, f'ejercicios/{enunciado.id_enun_ejercicio}')
            os.makedirs(carpeta_destino, exist_ok=True)

            print('6:Carpeta destino creada:', carpeta_destino)
            # 6. Extraer ZIP
            with zipfile.ZipFile(zip_absoluto, 'r') as zip_ref:
                zip_ref.extractall(carpeta_destino)

            print('7:ZIP extraído en:', carpeta_destino)
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

            print('8:ZIP eliminado:', zip_absoluto)
            # 8. Ejecutar OCR
            transcripciones = procesar_ocr(carpeta_destino)

            print('Depurar OCR:', transcripciones)

            # 9. Ejecutar corrección de errores — CAMBIO AQUÍ
            errores_generados = detectar_errores(transcripciones, enunciado)

            print('Depurar errores generados:', errores_generados)

            print('9:Errores generados:', errores_generados)
            request.session['datos_para_paso2'] = {
                'nombre': nombre_ejercicio,
                'asignatura': asignatura,
                'convocatoria': convocatoria,
                'fecha_examen_str': fecha_realizacion,
                'id_enunciado_ejercicio': enunciado.id_enun_ejercicio,
            }

            return HttpResponseRedirect('/correccion-ejercicio-paso2/')

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
    def post(self, request, pk):
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


def register_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Solo el superusuario puede crear nuevos usuarios.")
    # código para crear usuario


def login_view(request):
    return render(request, 'app/login.html')


@login_required
def eleccion_menu(request):
    return render(request, 'eleccion_menu.html', {
        'username': request.user.username
    })

def eleccion_menu(request):
    return render(request, 'core/eleccion_menu.html', {
        'username': request.user.username,
        'is_superuser': request.user.is_superuser  # Verifica si el usuario es superuser
    })

@login_required # Requiere que el usuario esté logueado
def corregir_ejercicio_carga_view(request):
    """
    Vista para mostrar la página de carga de ejercicios para corregir.
    """
    # Aquí podrías obtener datos para los datalists si lo deseas
    # Ejemplo (necesitarías importar los modelos):
    # asignaturas_existentes = Asignatura.objects.values_list('nombre', flat=True).distinct()
    # enunciados_existentes = Enunciado.objects.values_list('titulo', flat=True).distinct()
    # ... etc ...
    try:
        asignaturas_existentes = Examen.objects.values_list('asignatura', flat=True).distinct().order_by('asignatura')
        nombres_ejercicio_existentes = EnunciadoEjercicio.objects.values_list('nombre_ejercicio', flat=True).distinct().order_by('nombre_ejercicio')

    except Exception as e:
        # Manejo básico de errores por si la tabla/campo no existe o hay otro problema
        print(f"Error al obtener datos para datalists: {e}")

    context = {
        'username': request.user.username, # Pasa el username para el header
        'is_superuser': request.user.is_superuser, # Por si necesitas lógica específica en plantilla
        # 'asignaturas': list(asignaturas_existentes), # Descomenta y adapta si cargas datos
        'lista_asignaturas': list(asignaturas_existentes),
        'lista_nombres_ejercicio': list(nombres_ejercicio_existentes),
    }
    # Renderiza la nueva plantilla HTML que creaste
    return render(request, 'core/ce_1_carga.html', context)



# Asegúrate de tener estos imports al principio de tu views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import datetime # Para manejar la fecha

# ... (tus otras vistas como eleccion_menu, corregir_ejercicio_carga_view, etc. se quedan igual) ...

@login_required
def procesar_carga_y_redirigir_a_paso2_view(request):
    if request.method == 'POST':
        # 1. Recoge los datos del formulario (asegúrate que los 'name' en HTML coincidan)
        datos_formulario = {
            'nombre': request.POST.get('nombre_ejercicio', 'Ejercicio Sin Nombre'),
            'asignatura': request.POST.get('asignatura', 'Asignatura Desconocida'),
            'convocatoria': request.POST.get('convocatoria_tipo', 'Convocatoria Desconocida'),
            'fecha_examen_str': request.POST.get('fecha_examen', ''), # Se guarda como string
        }

        # 2. Guarda el diccionario completo en la sesión con una clave clara
        request.session['datos_para_paso2'] = datos_formulario
        
        # (Opcional) Imprime en la consola de Django para verificar qué se guardó
        print(f"Datos guardados en sesión: {request.session['datos_para_paso2']}")

        return redirect('vista_mostrar_paso2_correccion') # Redirige a la vista del paso 2
    
    # Si no es POST, volver a la página de carga del paso 1
    return redirect('vista_paso1_carga') # Usa el name de la URL de tu vista corregir_ejercicio_carga_view

from core.models import Error, EjercicioAlumno, AlumnoErrorEjercicio  # Ajusta import según tu estructura

@login_required
def mostrar_paso2_correccion_view(request):
    datos_recibidos = request.session.pop('datos_para_paso2', None)

    ejercicio_actual = {}
    if datos_recibidos:
        fecha_obj = None
        if datos_recibidos.get('fecha_examen_str'):
            try:
                fecha_obj = datetime.datetime.strptime(datos_recibidos['fecha_examen_str'], '%Y-%m-%d').date()
            except ValueError:
                pass

        ejercicio_actual = {
            'nombre': datos_recibidos.get('nombre'),
            'asignatura': datos_recibidos.get('asignatura'),
            'convocatoria': datos_recibidos.get('convocatoria'),
            'fecha_examen': fecha_obj,
        }

        # Consulta errores reales relacionados con este ejercicio
        # Asumiendo que tienes la relación para filtrar errores relacionados
        
        id_enunciado = datos_recibidos.get('id_enunciado_ejercicio')
        errores = Error.objects.filter(alumnoerrorejercicio__ejercicio_alumno__enunciado__id_enun_ejercicio=id_enunciado).distinct()

        errores_lista = []

        for error in errores:
            # Contar cuántos alumnos tienen este error en ejercicios relacionados
            num_alumnos = AlumnoErrorEjercicio.objects.filter(error=error).values('alumno').distinct().count()
            errores_lista.append({
                'id': error.id_error,
                'descripcion': error.descripcion,
                'penalizacion_gpt': error.penalizacion_llm,
                'penalizacion_profesor': error.penalizacion_prof,
                'num_alumnos': num_alumnos,
            })
    else:
        ejercicio_actual = {
            'nombre': 'Ejercicio (Datos no encontrados)',
            'asignatura': 'Asignatura (Datos no encontrados)',
            'convocatoria': 'Convocatoria (Datos no encontrados)',
            'fecha_examen': None,
        }
        errores_lista = []

    context = {
        'username': request.user.username,
        'is_superuser': request.user.is_superuser,
        'ejercicio': ejercicio_actual,
        'errores_lista': errores_lista,
    }
    return render(request, 'core/ce_2_carga.html', context)


# En core/views.py
@login_required
def mostrar_paso3_validacion_ocr_view(request):
    # Por ahora, no se necesita pasar datos específicos del ejercicio,
    # ya que la plantilla usa datos de ejemplo en su JS.
    # Cuando integres el backend, aquí cargarías los datos reales
    # del ejercicio y sus imágenes/textos OCR.
    context = {
        'username': request.user.username,
        'is_superuser': request.user.is_superuser,
        # 'ejercicio': datos_del_ejercicio_actual, # Descomentar cuando tengas los datos
    }
    return render(request, 'core/ce_3_validacion_ocr.html', context)


@login_required
def mostrar_paso4_correccion_final_view(request):
    # Por ahora, no se necesita pasar un contexto muy complejo,
    # solo lo que necesite base_ce.html (username, is_superuser)
    # y cualquier dato placeholder que quieras mostrar.
    context = {
        'username': request.user.username,
        'is_superuser': request.user.is_superuser,
        # Podrías pasar datos del ejercicio si los recuperas de la sesión o BD
        # 'ejercicio': datos_del_ejercicio_actual, 
    }
    return render(request, 'core/ce_4_correccion_errores.html', context)

@login_required # Opcional, pero recomendable si es información sensible
def mostrar_historial_correcciones_view(request):
    """
    Muestra la página de Historial de Correcciones (ce_5_historial_correcciones.html).
    Por ahora, no pasará datos de historial a la plantilla, ya que la tabla
    se llenará inicialmente con un mensaje o datos de ejemplo desde JavaScript.
    En el futuro, esta vista podría recuperar y pasar datos filtrados.
    """
    context = {
        'username': request.user.username,
        'is_superuser': request.user.is_superuser,
        # Aquí podrías pasar listas para poblar los <select> de los filtros si los tuvieras,
        # por ejemplo, todas las asignaturas únicas, convocatorias, etc.
        # 'lista_todas_asignaturas': Asignatura.objects.values_list('nombre', flat=True).distinct(),
        # 'lista_todas_convocatorias': Examen.objects.values_list('convocatoria', flat=True).distinct(),
    }
    # Asegúrate que la ruta 'core/ce_5_historial_correcciones.html' sea correcta
    return render(request, 'core/ce_5_historial_correcciones.html', context)

from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.db import transaction
import json
from .models import Error
@method_decorator(csrf_protect, name='dispatch') # O ensure_csrf_cookie si prefieres
class ActualizarPenalizacionesProfesorView(View):
    def post(self, request, *args, **kwargs):
        try:
            # El frontend enviará los datos como JSON
            data = json.loads(request.body)
            penalizaciones_actualizar = data.get('penalizaciones')

            if not isinstance(penalizaciones_actualizar, list):
                return JsonResponse({'error': 'Formato de datos inválido.'}, status=400)

            errores_actualizados_ids = []
            errores_no_encontrados_ids = []
            errores_valor_invalido_ids = []

            with transaction.atomic(): # Para asegurar que todas las actualizaciones se hagan o ninguna
                for item in penalizaciones_actualizar:
                    error_id = item.get('id_error')
                    nueva_penalizacion_str = item.get('penalizacion_prof')

                    if error_id is None or nueva_penalizacion_str is None:
                        # Considera cómo manejar esto, quizás añadir a una lista de errores parciales
                        continue

                    try:
                        error_obj = Error.objects.get(pk=error_id)
                        
                        # Validar y convertir la nueva penalización
                        try:
                            nueva_penalizacion = float(nueva_penalizacion_str)
                            if not (0 <= nueva_penalizacion <= 10): # Asumiendo tu validación min/max
                                raise ValueError("Penalización fuera de rango.")
                        except ValueError:
                            errores_valor_invalido_ids.append(error_id)
                            continue # Saltar este error y continuar con el siguiente

                        error_obj.penalizacion_prof = nueva_penalizacion
                        error_obj.save()
                        errores_actualizados_ids.append(error_id)

                    except Error.DoesNotExist:
                        errores_no_encontrados_ids.append(error_id)
            
            # Construir una respuesta informativa
            response_data = {
                'mensaje': 'Proceso de actualización completado.',
                'actualizados': len(errores_actualizados_ids),
                'no_encontrados': errores_no_encontrados_ids,
                'valor_invalido': errores_valor_invalido_ids
            }
            status_code = 200
            if errores_no_encontrados_ids or errores_valor_invalido_ids:
                status_code = 207 # Multi-Status, indica éxito parcial

            return JsonResponse(response_data, status=status_code)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Cuerpo de la solicitud no es JSON válido.'}, status=400)
        except Exception as e:
            # Considera loggear el error 'e' en el servidor
            return JsonResponse({'error': f'Ocurrió un error inesperado: {str(e)}'}, status=500)
