# login/forms.py
from django.contrib.auth.models import User  # Modelo de usuario por defecto
from django import forms
from django.contrib.auth.forms import UserCreationForm

class FormularioRegistro(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User  # <-- Usar el modelo User por defecto
        fields = ['username', 'email', 'password1', 'password2']

class FormularioLogin(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)