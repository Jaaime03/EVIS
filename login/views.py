from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.utils import timezone
from .models import LoginAttempt

def login_view(request):
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # 1) Bloquear todo hasta que exista el root
        if not User.objects.filter(is_superuser=True).exists():
            error = 'La aplicación aún no está inicializada. Contacta con el administrador.'
            return render(request, 'login/index.html', {'error': error})

        # Fecha de hoy
        today = timezone.now().date()
        # 2) Obtener o crear el contador para este email+hoy
        attempt, _ = LoginAttempt.objects.get_or_create(email=email, date=today)

        # 3) Si ya 10 fallos, denegamos directamente
        if attempt.fails >= 10:
            error = 'Has excedido los 10 intentos de acceso de hoy para este usuario. Vuelve mañana.'
            return render(request, 'login/index.html', {'error': error})

        # 4) Intentamos autenticar: buscamos user por email
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            user = None

        # 5) Validación de contraseña
        if user and user.check_password(password):
            # ¡Éxito! Reseteamos el contador y lo logueamos
            attempt.fails = 0
            attempt.save()
            auth_login(request, user)
            return redirect('eleccion_menu')
        else:
            # Fallo: incrementamos contador y mostramos error
            attempt.fails += 1
            attempt.save()
            error = 'Correo o contraseña incorrecta.'

    return render(request, 'login/index.html', {'error': error})
