import json
import os
import re
import base64
from openai import AzureOpenAI
from dotenv import load_dotenv
import django
from core.models import EjercicioAlumno, Error, AlumnoErrorEjercicio, Alumno, EnunciadoEjercicio

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

def codificar_imagen_base64(ruta_imagen):
    with open(ruta_imagen, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def detectar_errores_individuales(transcripciones: dict, enunciado_obj: EnunciadoEjercicio, client) -> dict:
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
                        "Eres un sistema de análisis automático de respuestas SQL de alumnos.\n"
                        "Recibirás:\n"
                        "   a. El enunciado del ejercicio.\n"
                        "   b. Una imagen con la estructura de tablas asociada.\n"
                        "   c. Las respuestas de varios alumnos, con el formato JSON:\n"
                        "      {\n"
                        "        \"ID_alumno\": { \"ejercicio\": \"respuesta\" },\n"
                        "        …\n"
                        "      }\n\n"
                        "Para cada alumno, analiza su respuesta por separado y extrae los errores concretos que comete.\n"
                        "No agrupes ni generalices. No compares entre alumnos.\n\n"
                        "Devuelve un JSON:\n"
                        "{\n"
                        "  \"ID_alumno\": [\"error 1\", \"error 2\", ...],\n"
                        "  ...\n"
                        "}\n\n"
                        "Datos de entrada\n"
                        f"Enunciado del ejercicio:\n{enunciado_obj.enunciado_ejerc}\n\n"
                        f"Respuestas de los alumnos:\n{respuestas}\n"
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

    print("Respuesta del modelo recibida.")

    content = response.choices[0].message.content
    match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    else:
        raise ValueError("No se pudo obtener el JSON de errores individuales.")
    

def agrupar_errores_por_concepto(errores_por_alumno: dict, client) -> dict:
    errores_texto = "\n".join(
        f"{alumno_id}: {error}"
        for alumno_id, errores in errores_por_alumno.items()
        for error in errores
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "A continuación recibirás una lista de errores cometidos por diferentes alumnos, en forma de JSON:\n"
                        "{\n"
                        "  \"ID_alumno\": [\"error 1\", \"error 2\", ...],\n"
                        "  ...\n"
                        "}\n\n"
                        "Tu tarea es AGRUPAR errores similares en cuanto a concepto, incluso si están escritos diferente.\n"
                        "Genera un JSON donde cada grupo tiene:\n"
                        "- Una 'descripcion' general del error común\n"
                        "- Una 'penalizacion_llm' (valor numérico de 0 a 10) dependiendo de la gravedad del error\n"
                        "- Una lista de 'ID alumnos' que cometen ese error\n\n"
                        "Formato de salida:\n"
                        "Devuelve SOLO un JSON con claves numéricas consecutivas (enteros), p. ej.:\n"
                        "{\n"
                        "   \"1\"{\n"
                        "     \"descripcion\": \"Breve explicación del error\",\n"
                        "     \"penalizacion_llm\": ej.0.5,\n"
                        "     \"alumnos\": [\"ej.A123\", \"ej.B456\"]\n"
                        "   },\n"
                        "   \"2\"{\n"
                        "       ..."
                        "   }\n"
                        "}\n\n"
                        "Datos de entrada"
                        f"Errores:\n{errores_texto}"
                    )
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
        return json.loads(match.group(1))
    else:
        raise ValueError("No se pudo obtener el JSON agrupado de errores.")


def detectar_errores(transcripciones: dict, enunciado_obj: EnunciadoEjercicio) -> dict:
    errores_individuales = detectar_errores_individuales(transcripciones, enunciado_obj, client)
    errores_agrupados = agrupar_errores_por_concepto(errores_individuales, client)

    print("Guardando errores agrupados en la base de datos...")
    for id_error, contenido in errores_agrupados.items():
        descripcion = contenido.get("descripcion", "").strip()
        penalizacion_llm = contenido.get("penalizacion_llm", 0)
        alumnos_con_error = contenido.get("alumnos", [])

        try:
            error = Error.objects.create(
                descripcion=descripcion,
                penalizacion_llm=penalizacion_llm,
                penalizacion_prof=0
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

    return errores_agrupados