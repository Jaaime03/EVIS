import os
import zipfile

from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, parser_classes

from django.conf import settings
from .models import Examen, EnunciadoEjercicio, EjercicioAlumno, Error, Alumno, AlumnoErrorEjercicio
from .serializers import ExamenSerializer, EnunciadoEjercicioSerializer, EjercicioAlumnoSerializer, ErrorSerializer, AlumnoSerializer, AlumnoErrorEjercicioSerializer
from utils.procesar_ocr import procesar_ocr
from utils.detectar_errores import detectar_errores


@api_view(['POST'])
def crear_examen(request):
    """Crear un nuevo examen."""
    if request.method == 'POST':
        serializer = ExamenSerializer(data=request.data)
        if serializer.is_valid():
            examen = serializer.save()
            return Response({'id_examen': examen.id_examen}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def crear_enunciado_ejercicio(request):
    """Crear un nuevo enunciado de ejercicio para un examen existente."""
    if request.method == 'POST':
        examen_id = request.data.get('examen_id')
        try:
            examen = Examen.objects.get(id_examen=examen_id)
        except Examen.DoesNotExist:
            return Response({'error': 'Examen no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ahora añadimos el enunciado del ejercicio
        data = request.data
        data['examen'] = examen.id_examen 
        serializer = EnunciadoEjercicioSerializer(data=data)
        if serializer.is_valid():
            enunciado = serializer.save()
            return Response({'id_enunciado_ejercicio': enunciado.id_enun_ejercicio}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@parser_classes([MultiPartParser])
def subir_imagenes_ejercicio(request):
    """
    Recibe un archivo ZIP con imágenes, las descomprime y las guarda en una carpeta nombrada con el id_enun_ejercicio.
    """
    zip_file = request.FILES.get('archivo')
    id_enun_ejercicio = request.POST.get('id_enun_ejercicio')

    if not zip_file or not id_enun_ejercicio:
        return Response({"error": "Se requiere un archivo ZIP y un id_enun_ejercicio."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        enunciado = EnunciadoEjercicio.objects.get(id_enun_ejercicio=id_enun_ejercicio)
    except EnunciadoEjercicio.DoesNotExist:
        return Response({"error": "EnunciadoEjercicio no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    # Crear ruta donde se guardarán las imágenes
    carpeta_destino = os.path.join(settings.MEDIA_ROOT, 'ejercicios', str(id_enun_ejercicio))
    os.makedirs(carpeta_destino, exist_ok=True)

    # Guardar ZIP temporalmente y descomprimir
    zip_path = os.path.join(carpeta_destino, "temp.zip")
    with open(zip_path, 'wb+') as f:
        for chunk in zip_file.chunks():
            f.write(chunk)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(carpeta_destino)

    os.remove(zip_path)  # Eliminar el zip después de extraer

    # Crear EjercicioAlumno para cada imagen
    creados = 0
    for archivo in sorted(os.listdir(carpeta_destino)):
        if archivo.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                id_alumno = int(os.path.splitext(archivo)[0])
                alumno = Alumno.objects.get(id_alumno=id_alumno)

                ruta_web = os.path.join('ejercicios', str(id_enun_ejercicio), archivo)
                ejercicio = EjercicioAlumno.objects.create(
                    enunciado=enunciado,
                    url_foto_ejerc=os.path.join(settings.MEDIA_URL, ruta_web),
                    ocr_imag_to_text="",
                    correcto_ocr=False,
                    correccion_ocr_hum="",
                    calif_profesor_solo=0,
                    alumno=alumno 
                )
                creados += 1
            except Alumno.DoesNotExist:
                continue
            except Exception as e:
                print(f"Error creando EjercicioAlumno para {archivo}: {e}")

    return Response({"mensaje": f"Imágenes procesadas correctamente. {creados} ejercicios creados."}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def procesar_ocr_api(request):
    """
    Procesa las imágenes almacenadas localmente en una carpeta específica.
    Se debe proporcionar el id_enun_ejercicio (la carpeta se espera en media/ejercicios/<id_enun_ejercicio>).
    """
    id_enun_ejercicio = request.data.get('id_enun_ejercicio')
    if not id_enun_ejercicio:
        return Response({"error": "Se requiere el id_enun_ejercicio."}, status=status.HTTP_400_BAD_REQUEST)

    carpeta = os.path.join(settings.MEDIA_ROOT, 'ejercicios', str(id_enun_ejercicio))
    if not os.path.exists(carpeta):
        return Response({"error": f"No existe la carpeta de imágenes para el ejercicio {id_enun_ejercicio}."}, status=status.HTTP_404_NOT_FOUND)

    try:
        resultados = procesar_ocr(carpeta)
        return Response({"mensaje": "OCR procesado correctamente", "resultados": resultados}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def procesar_correccion_api(request):
    """
    Procesa la corrección automática de errores a partir del id_enun_ejercicio.
    Usa las transcripciones ya guardadas en EjercicioAlumno.
    """
    id_enun_ejercicio = request.data.get("id_enun_ejercicio")

    if not id_enun_ejercicio:
        return Response({"error": "Se requiere el id_enun_ejercicio."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        enunciado = EnunciadoEjercicio.objects.get(id_enun_ejercicio=id_enun_ejercicio)
    except EnunciadoEjercicio.DoesNotExist:
        return Response({"error": "EnunciadoEjercicio no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    ejercicios = EjercicioAlumno.objects.filter(enunciado=enunciado, correcto_ocr=True)

    if not ejercicios.exists():
        return Response({"error": "No hay ejercicios con OCR correcto para este enunciado."}, status=status.HTTP_400_BAD_REQUEST)

    # Construir el diccionario esperado por detectar_errores
    transcripciones = {
        str(ej.alumno.id_alumno): {"ejercicio": ej.ocr_imag_to_text}
        for ej in ejercicios
    }

    try:
        errores = detectar_errores(
            transcripciones=transcripciones,
            enunciado=enunciado.enunciado,
            tablas=enunciado.estructura_tablas
        )
        return Response({"mensaje": "Corrección completada", "errores": errores}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
