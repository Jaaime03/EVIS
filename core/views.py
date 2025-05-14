import datetime
from rest_framework.viewsets import ModelViewSet

from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.models import EnunciadoEjercicio, Examen

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

@login_required
def mostrar_paso2_correccion_view(request):
    # 1. Recupera el diccionario de la sesión (usa .pop() para limpiarlo después de usarlo)
    datos_recibidos = request.session.pop('datos_para_paso2', None)

    # (Opcional) Imprime en la consola de Django para verificar qué se recuperó
    print(f"Datos recuperados de sesión para Paso 2: {datos_recibidos}")

    ejercicio_actual = {}
    if datos_recibidos:
        # Intenta convertir la fecha si existe
        fecha_obj = None
        if datos_recibidos.get('fecha_examen_str'):
            try:
                fecha_obj = datetime.datetime.strptime(datos_recibidos['fecha_examen_str'], '%Y-%m-%d').date()
            except ValueError:
                pass # La fecha se queda como None si hay error

        ejercicio_actual = {
            'nombre': datos_recibidos.get('nombre'),
            'asignatura': datos_recibidos.get('asignatura'),
            'convocatoria': datos_recibidos.get('convocatoria'),
            'fecha_examen': fecha_obj,
        }
    else:
        # Si no hay datos en sesión (ej. se accedió a la URL directamente), usa placeholders
        print("No se encontraron datos en sesión para Paso 2. Usando placeholders.")
        ejercicio_actual = {
            'nombre': 'Ejercicio (Datos no encontrados)',
            'asignatura': 'Asignatura (Datos no encontrados)',
            'convocatoria': 'Convocatoria (Datos no encontrados)',
            'fecha_examen': None,
        }

    # La lista de errores puede seguir siendo placeholder
    errores_lista_placeholder = [
        {'id': "ErrTMP-01", 'descripcion': 'Error de ejemplo 1', 'penalizacion_gpt': -0.3, 'num_alumnos': 5, 'penalizacion_profesor': None},
        {'id': "ErrTMP-02", 'descripcion': 'Error de ejemplo 2', 'penalizacion_gpt': -0.8, 'num_alumnos': 2, 'penalizacion_profesor': None},
    ]

    context = {
        'username': request.user.username,
        'is_superuser': request.user.is_superuser,
        'ejercicio': ejercicio_actual, # Aquí van los datos recuperados o los placeholders
        'errores_lista': errores_lista_placeholder,
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