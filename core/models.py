from django.db import models

class Examen(models.Model):
    id_examen = models.AutoField(primary_key=True)
    fecha_realizacion = models.DateField()
    asignatura = models.CharField(max_length=100)
    convocatoria = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.asignatura} - {self.convocatoria}"


class EnunciadoEjercicio(models.Model):
    id_enun_ejercicio = models.AutoField(primary_key=True)
    puntuacion_ejercicio = models.FloatField()
    enunciado_ejerc = models.TextField()
    estructura_tablas = models.ImageField(upload_to='estructura_tablas/', blank=True, null=True)
    nombre_ejercicio = models.CharField(max_length=255)
    examen = models.ForeignKey(Examen, on_delete=models.PROTECT, related_name='enunciados')

    def __str__(self):
        return self.nombre_ejercicio


class Alumno(models.Model):
    id_alumno = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=200)
    matricula = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    dni = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"
    

class EjercicioAlumno(models.Model):
    id_ejercicio_alum = models.AutoField(primary_key=True)
    enunciado = models.ForeignKey(EnunciadoEjercicio, on_delete=models.PROTECT, related_name='ejercicios_alumno')
    alumno = models.ForeignKey(Alumno, on_delete=models.PROTECT, related_name='ejercicios_alumno')
    url_foto_ejerc = models.URLField(max_length=500)
    ocr_imag_to_text = models.TextField(blank=True, null=True)
    correcto_ocr = models.BooleanField(default=False)
    correccion_ocr_hum = models.TextField(blank=True, null=True)
    calif_profesor_solo = models.FloatField(blank=True, null=True)
    estado = models.CharField(max_length=50, default='pendiente')

    def __str__(self):
        return f"EjercicioAlumno {self.id_ejercicio_alum}"


class Error(models.Model):
    id_error = models.AutoField(primary_key=True)
    descripcion = models.TextField()
    penalizacion_llm = models.FloatField()
    penalizacion_prof = models.FloatField()

    def __str__(self):
        return f"Error {self.id_error}"


class AlumnoErrorEjercicio(models.Model):
    id = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.PROTECT)
    error = models.ForeignKey(Error, on_delete=models.PROTECT)
    ejercicio_alumno = models.ForeignKey(EjercicioAlumno, on_delete=models.PROTECT)
    situacion = models.CharField(max_length=50, choices=[
        ('Correcto', 'Correcto'),
        ('Incorrecto', 'Incorrecto'),
        ('Anadido', 'Añadido')
    ])

    class Meta:
        unique_together = ('alumno', 'error', 'ejercicio_alumno')

    def __str__(self):
        return f"{self.alumno} - {self.error} - {self.ejercicio_alumno} ({self.situacion})"