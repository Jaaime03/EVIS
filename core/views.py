from rest_framework.viewsets import ModelViewSet

from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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