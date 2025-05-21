import base64
import os
import json
import re
import logging
from openai import AzureOpenAI
from dotenv import load_dotenv
import django
from core.models import EjercicioAlumno, Alumno

# Cargar entorno y configurar Django
load_dotenv(override=True)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "evis_project.settings")
django.setup()

# Configuración Azure
client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
)

logger = logging.getLogger(__name__)

def procesar_ocr(carpeta_imagenes: str) -> dict:
    imagenes_contenido = []
    nombres_procesados = []

    print("Procesando imágenes en la carpeta:", carpeta_imagenes)
    for archivo in sorted(os.listdir(carpeta_imagenes)):
        if archivo.lower().endswith((".jpg", ".jpeg", ".png")):
            ruta = os.path.join(carpeta_imagenes, archivo)
            with open(ruta, "rb") as f:
                imagen_base64 = base64.b64encode(f.read()).decode("utf-8")
                imagenes_contenido.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{imagen_base64}"
                    }
                })
                nombres_procesados.append(archivo)

    print("Imágenes procesadas:", nombres_procesados)
    instruccion = (
        "Te voy a enviar varias imágenes de texto manuscrito. "
        "Cada imagen tiene un nombre como '123.jpg', donde '123' es el ID del alumno. "
        "Transcribe exactamente el texto manuscrito de cada imagen (sin corregir errores) y devuélvelo en un JSON con esta estructura:\n\n"
        "{\n"
        "  \"123\": {\n"
        "    \"ejercicio\": \"texto...\"\n"
        "  },\n"
        "  \"456\": {\n"
        "    \"ejercicio\": \"...\"\n"
        "  }\n"
        "}\n\n"
        f"Las imágenes que te envío son: {', '.join(nombres_procesados)}"
    )
    print(f"Endpoint de Azure: {os.environ.get('AZURE_OPENAI_ENDPOINT')}")
    print(f"API Key de Azure (primeros 5 caracteres): {os.environ.get('AZURE_OPENAI_API_KEY', '')[:5]}") # Solo imprime una parte por seguridad

    print("Instrucción enviada al modelo:", instruccion)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": instruccion},
                *imagenes_contenido  # Desempaqueta la lista de imágenes aquí
            ]
        }],
        max_tokens=4000
    )
    print("Respuesta del modelo recibida.") # Esta línea ahora solo se ejecutará si no hay error
    # Procesa la respuesta
    # print(response.choices[0].message.content)

    respuesta_texto = response.choices[0].message.content

    match = re.search(r"```json\s*(.*?)\s*```", respuesta_texto, re.DOTALL)
    if not match:
        logger.error("OCR: No se encontró un bloque JSON válido.")
        raise ValueError("OCR: No se encontró un bloque JSON válido.")

    try:
        resultados = json.loads(match.group(1))
    except json.JSONDecodeError:
        logger.error("OCR: JSON generado no válido.")
        raise ValueError("OCR: JSON generado no válido.")

    print("Guardando OCR en la base de datos...")
    # GUARDADO EN BASE DE DATOS
    for id_alumno_str, contenido in resultados.items():
        try:
            id_alumno = int(id_alumno_str)
            texto = contenido.get("ejercicio", "").strip()
            alumno = Alumno.objects.get(id_alumno=id_alumno)
            ejercicios = EjercicioAlumno.objects.filter(alumno=alumno).latest('id_ejercicio_alum')

            if not ejercicios:
                logger.warning(f"No se encontraron ejercicios para el alumno {id_alumno}")
                continue

            ejercicio = ejercicios
            ejercicio.ocr_imag_to_text = texto
            ejercicio.correcto_ocr = True
            ejercicio.save()
            logger.info(f"OCR guardado para alumno {id_alumno} en ejercicio {ejercicio.id_ejercicio_alum}")

        except Alumno.DoesNotExist:
            logger.error(f"Alumno con ID {id_alumno_str} no encontrado.")
        except Exception as e:
            logger.error(f"Error al guardar OCR para {id_alumno_str}: {e}")

    print("OCR guardado en la base de datos.")
    print("Resultados del OCR:", resultados)
    return resultados
