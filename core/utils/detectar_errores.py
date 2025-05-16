import json
import os
import re
from openai import AzureOpenAI
from dotenv import load_dotenv
import django
from core.models import EjercicioAlumno, Error, AlumnoErrorEjercicio, Alumno

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

def detectar_errores(transcripciones: dict, enunciado: str, tablas:str) -> dict:
    respuestas = "\n".join(
        f"{alumno_id}: {contenido['ejercicio'].strip()}"
        for alumno_id, contenido in transcripciones.items()
    )

    prompt = (
        f"Eres un corrector automático de exámenes.\n"
        f"A continuación tienes el enunciado de un ejercicio, la estructura de tablas correspondiente y las respuestas de varios alumnos.\n\n"
        f"Tu tarea es identificar errores posibles entre estas respuestas. Por cada error encontrado, proporciona:\n"
        f"  - una breve descripción,\n"
        f"  - una penalización sobre 10,\n"
        f"  - la lista de ID de los alumnos que han cometido ese error.\n\n"
        f"Enunciado del ejercicio:\n{enunciado}\n\n"
        f"Estructura de tablas del ejercicio:\n{tablas}\n\n"
        f"Respuestas de los alumnos:\n{respuestas}\n\n"
        f"Devuelve solo un JSON con esta estructura (usa números enteros como clave):\n"
        "{\n"
        "  \"1\": {\n"
        "    \"descripcion\": \"...\",\n"
        "    \"penalizacion_llm\": 0.5,\n"
        "    \"alumnos\": [\"123\", \"456\"]\n"
        "  },\n"
        "  ...\n"
        "}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
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

        # Guardar el error
        try:
            error = Error.objects.create(
                descripcion=descripcion,
                penalizacion_llm=penalizacion_llm,
                penalizacion_prof=penalizacion_llm 
            )

            # Relacionar los alumnos con este error y la situación
            for alumno_id_str in alumnos_con_error:
                try:
                    alumno_id = int(alumno_id_str)
                    alumno = Alumno.objects.get(id_alumno=alumno_id)
                    ejercicios = EjercicioAlumno.objects.filter(alumno=alumno).order_by('-id_ejercicio_alum')

                    if not ejercicios.exists():
                        print(f"No se encontraron ejercicios para el alumno {alumno_id}")
                        continue

                    ejercicio = ejercicios.first()  # REVISAR
                    AlumnoErrorEjercicio.objects.create(
                        alumno=alumno,
                        error=error,
                        ejercicio_alumno=ejercicio,
                        situacion='Correcto'  # poner correcto por deecto?
                    )
                    print(f"Error guardado para alumno {alumno_id} en ejercicio {ejercicio.id_ejercicio_alum}")

                except Alumno.DoesNotExist:
                    print(f"Alumno con ID {alumno_id_str} no encontrado.")
                except Exception as e:
                    print(f"Error al guardar error para {alumno_id_str}: {e}")

        except Exception as e:
            print(f"Error al guardar el error {id_error}: {e}")

    return errores
