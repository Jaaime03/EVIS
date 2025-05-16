# EVIS - Evaluador Inteligente de Soluciones

EVIS es una plataforma web que permite subir fotos de ejercicios, aplicar OCR y correcciones automáticas mediante LLMs, y registrar correcciones humanas.
---

## 🚀 Tecnologías

- **Backend**: Django + Django REST Framework (Python)
- **Base de datos**: SQLite (por defecto, se puede cambiar en "producción")
- **Frontend**: HTML/CSS/JS 
- **OCR + LLM**: Integración futura

---

## ♻ Instalación local (Desarrollo)

### 1. Clona el repositorio
```bash
git clone https://github.com/tu_usuario/EVIS.git
cd EVIS
```

### 2. Crea y activa un entorno virtual
```bash
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
```

### 3. Instala las dependencias
```bash
pip install -r requirements.txt
```

### 4. Configura variables de entorno
Crea un archivo `.env` en la raíz del proyecto y pon tu clave secreta:
```env
DJANGO_SECRET_KEY=tu_clave_secreta
```

### 5. Aplica migraciones y crea la base de datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crea un superusuario
```bash
python manage.py createsuperuser
```

### 7. Ejecuta el servidor
```bash
python manage.py runserver
```

Accede desde tu navegador a: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔐 Seguridad

- No compartas la clave `SECRET_KEY` en público
- No subas `.env` al repositorio (está en `.gitignore`)
- Considera usar PostgreSQL y configuraciones adicionales para producción

---

## 📁 Estructura del proyecto

```
EVIS/
├── core/               # App principal
│   ├── models.py       # Modelos de base de datos
│   ├── views.py        # Vistas y API REST
│   ├── serializers.py  # Serializadores DRF
│   └── urls.py         # Rutas propias
├── EVIS/               # Configuración del proyecto Django
│   ├── settings.py     # Configuraciones globales
│   └── urls.py         # Rutas globales
├── manage.py
├── .env                # Variables de entorno (no subir)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚫 No olvides:

- Ignorar archivos sensibles y temporales con `.gitignore`
- Compartir el archivo `.env` solo por medios privados
- Actualizar `requirements.txt` si añades nuevas dependencias

---

## ✏️ Autor

Proyecto desarrollado por estudiantes de la UPM en colaboración con el CTB. Para más información o colaboraciones, contacta con los autores.
Alicia Guzman  
Jaime Capdepon Fraile           email:capdepon28@gmail.com 
