import json
import os
import re
import base64
from openai import AzureOpenAI
from dotenv import load_dotenv
import django
from core.models import EjercicioAlumno, Error, AlumnoErrorEjercicio, Alumno, EnunciadoEjercicio

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

def codificar_imagen_base64(ruta_imagen):
    with open(ruta_imagen, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def detectar_errores(transcripciones: dict, enunciado_obj: EnunciadoEjercicio) -> dict:
    respuestas = "\n".join(
        f"{alumno_id}: {contenido['ejercicio'].strip()}"
        for alumno_id, contenido in transcripciones.items()
    )

    # Codificar imagen base64 de estructura_tablas
    if not enunciado_obj.estructura_tablas:
        raise ValueError("El ejercicio no tiene imagen en estructura_tablas.")

    imagen_path = enunciado_obj.estructura_tablas.path
    imagen_base64 = codificar_imagen_base64(imagen_path)

    # Construcción del prompt
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Eres un corrector automático de exámenes.\n"
                        "A continuación tienes el enunciado de un ejercicio, una imagen con la estructura de tablas correspondiente y las respuestas de varios alumnos.\n\n"
                        "Tu tarea es identificar errores posibles entre estas respuestas. Por cada error encontrado, proporciona:\n"
                        "- una breve descripción,\n"
                        "- una penalización sobre 10,\n"
                        "- la lista de ID de los alumnos que han cometido ese error.\n\n"
                        f"Enunciado del ejercicio:\n{enunciado_obj.enunciado_ejerc}\n\n"
                        f"Respuestas de los alumnos:\n{respuestas}\n\n"
                        "Devuelve solo un JSON con esta estructura (usa números enteros como clave):\n"
                        "{\n"
                        "  \"1\": {\n"
                        "    \"descripcion\": \"...\",\n"
                        "    \"penalizacion_llm\": 0.5,\n"
                        "    \"alumnos\": [\"123\", \"456\"]\n"
                        "  },\n"
                        "  ...\n"
                        "}"
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{imagen_base64}"
                    }
                }
            ]
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=4000
    )

    content = response.choices[0].message.content

    match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        json_bloque = match.group(1)
        try:
            errores = json.loads(json_bloque)
        except json.JSONDecodeError:
            raise ValueError("Corrección: JSON generado no válido.")
    else:
        raise ValueError("Corrección: No se encontró un bloque JSON válido.")

    # GUARDADO EN BASE DE DATOS
    for id_error, contenido in errores.items():
        descripcion = contenido.get("descripcion", "").strip()
        penalizacion_llm = contenido.get("penalizacion_llm", 0)
        alumnos_con_error = contenido.get("alumnos", [])

        try:
            error = Error.objects.create(
                descripcion=descripcion,
                penalizacion_llm=penalizacion_llm,
                penalizacion_prof=penalizacion_llm
            )

            for alumno_id_str in alumnos_con_error:
                try:
                    alumno_id = int(alumno_id_str)
                    alumno = Alumno.objects.get(id_alumno=alumno_id)
                    ejercicios = EjercicioAlumno.objects.filter(alumno=alumno, enunciado=enunciado_obj).order_by('-id_ejercicio_alum')

                    if not ejercicios.exists():
                        print(f"No se encontraron ejercicios para el alumno {alumno_id}")
                        continue

                    ejercicio = ejercicios.first()
                    AlumnoErrorEjercicio.objects.create(
                        alumno=alumno,
                        error=error,
                        ejercicio_alumno=ejercicio,
                        situacion='Correcto' 
                    )
                    print(f"Error guardado para alumno {alumno_id} en ejercicio {ejercicio.id_ejercicio_alum}")

                except Alumno.DoesNotExist:
                    print(f"Alumno con ID {alumno_id_str} no encontrado.")
                except Exception as e:
                    print(f"Error al guardar error para {alumno_id_str}: {e}")

        except Exception as e:
            print(f"Error al guardar el error {id_error}: {e}")

    return errores