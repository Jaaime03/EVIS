from rest_framework.viewsets import ModelViewSet
from .models import Alumno
from .serializers import AlumnoSerializer

class AlumnoViewSet(ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
