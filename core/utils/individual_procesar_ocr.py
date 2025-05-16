import base64
import os
import logging
from openai import AzureOpenAI
from dotenv import load_dotenv
import django
from core.models import EjercicioAlumno, Alumno

# Cargar entorno y configurar Django
load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "evis_project.settings")
django.setup()

# Configuración Azure
client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
)

logger = logging.getLogger(__name__)

def codificar_imagen_base64(ruta_imagen):
    with open(ruta_imagen, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def individual_procesar_ocr(carpeta_imagenes, enunciado):
    resultados = {}
    imagenes = [f for f in os.listdir(carpeta_imagenes) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    for nombre_archivo in imagenes:
        id_alumno_str = os.path.splitext(nombre_archivo)[0]
        ruta = os.path.join(carpeta_imagenes, nombre_archivo)
        try:
            imagen_base64 = codificar_imagen_base64(ruta)

            respuesta = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Transcribe el contenido del ejercicio de esta imagen."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{imagen_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )

            texto = respuesta["choices"][0]["message"]["content"].strip()

            # Guardado en base de datos directamente
            alumno = Alumno.objects.get(id_alumno=int(id_alumno_str))
            ejercicio = EjercicioAlumno.objects.filter(alumno=alumno, enunciado=enunciado).latest('id_ejercicio_alum')

            ejercicio.ocr_imag_to_text = texto
            ejercicio.correcto_ocr = True
            ejercicio.save()

            resultados[id_alumno_str] = {"ejercicio": texto}

        except Alumno.DoesNotExist:
            logger.error(f"Alumno con ID {id_alumno_str} no encontrado.")
        except Exception as e:
            logger.error(f"Error procesando imagen {nombre_archivo}: {e}")
    
    return resultados