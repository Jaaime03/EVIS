# login/urls.py
from django.urls import path
from .views import login_view

urlpatterns = [
    path('', login_view, name='login'),  # http://localhost:8000/login/
]
