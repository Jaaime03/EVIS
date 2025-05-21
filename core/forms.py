# core/forms.py
from django import forms

class EnunciadoEjercicioForm(forms.Form):
    nombre_ejercicio = forms.CharField(label="Nombre Ejercicio", max_length=255, required=True)
    asignatura = forms.CharField(label="Asignatura", max_length=100, required=True)
    convocatoria = forms.CharField(label="Convocatoria", max_length=100, required=True)
    fecha_realizacion = forms.DateField(label="Fecha examen", required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    puntuacion_ejercicio = forms.FloatField(label="Puntuación Ejercicio", min_value=0, required=True)
    
    enunciado_txt = forms.FileField(label="Enunciado (.txt)", required=True, allow_empty_file=False)
    estructura_tablas_img = forms.ImageField(label="Estructura tablas (.png, .jpeg, .jpg)", required=False) # Asumiendo que puede ser opcional
    
    # Este campo es para el ZIP de las fotos de los ejercicios de los alumnos,
    # que procesarás en el paso 2.
    zip_fotos_ejercicios = forms.FileField(label="Carpeta Fotos Ejercicios (.zip)", required=True, allow_empty_file=False)

    def clean_enunciado_txt(self):
        file = self.cleaned_data.get('enunciado_txt')
        if file:
            if not file.name.endswith('.txt'):
                raise forms.ValidationError("El archivo del enunciado debe ser un .txt")
            # Puedes añadir más validaciones de tamaño o contenido si es necesario
        return file

    def clean_zip_fotos_ejercicios(self):
        file = self.cleaned_data.get('zip_fotos_ejercicios')
        if file:
            if not file.name.endswith('.zip'):
                raise forms.ValidationError("El archivo de fotos de ejercicios debe ser un .zip")
        return file