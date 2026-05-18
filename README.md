
# 🛡️ CyberQuest - Plataforma CTF de Ciberseguridad

Plataforma educativa para el aprendizaje de ciberseguridad con retos CTF (Capture The Flag), cursos interactivos, gestión de equipos y eventos en tiempo real.

---

## 👨‍💻 Autor

**Yhonatan Leonardo Mamani Torrez**

- Desarrollador Full Stack
- Especialista en Ciberseguridad y Django

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Uso](#-uso)
- [Roles y Permisos](#-roles-y-permisos)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)

---

## 🚀 Características

### Módulo 1: Administración de Usuarios
- Registro e inicio de sesión de usuarios
- Recuperación de contraseña por correo
- Perfiles personalizables con avatar
- Panel de administración (CRUD completo de usuarios)

### Módulo 2: Gestión de Equipos
- Creación de equipos con código de invitación
- Unirse a equipos existentes
- Visualización de miembros y estadísticas

### Módulo 3: Formación y Aprendizaje
- Módulos y lecciones educativas
- Sistema de progreso y puntuación
- Preguntas de verificación

### Módulo 4: Gestión de Retos CTF
- Retos por categorías y dificultades
- Sistema de banderas (flags)
- Entornos Docker integrados
- Filtros por categoría y dificultad

### Módulo 5: Control de Entornos
- Iniciar/Detener entornos Docker
- URLs dinámicas por contenedor
- Estado del entorno en tiempo real

### Módulo 6: Evaluación de Resultados
- Envío y validación de flags
- Puntuación automática
- Historial de intentos

### Módulo 7: Ranking y Clasificación
- Ranking individual de competidores
- Ranking por equipos
- Gráficas estadísticas con Chart.js
- Posición personal del usuario

### Módulo 8: Auditoría y Monitoreo
- Registro de todas las acciones
- Filtros por tipo y usuario
- Logs de inicio/cierre de sesión
- Registro de creaciones, ediciones y eliminaciones

### Módulo 9: Asistente IA
- Chatbot integrado
- Respuestas inteligentes desde base de datos
- Activación/desactivación por Admin
- Límite de consultas por día

### Módulo 10: Eventos CTF
- Creación de eventos
- Inscripción de participantes
- Retos exclusivos por evento
- Puntuación específica por evento

---

## 📦 Requisitos del Sistema

- Python 3.12 o superior
- Docker (para entornos de laboratorio)
- SQLite3 (base de datos por defecto)
- Navegador web moderno

---

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/yhonatan/cyberquest.git
cd cyberquest
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear archivo `.env` en la raíz:

```env
# Django
SECRET_KEY=tu_secret_key_aqui
DEBUG=True

# Email (para recuperación de contraseña)
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña

# Hugging Face API (para asistente IA)
HF_TOKEN=tu_token_aqui
```

### 5. Ejecutar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear superusuario (Admin)

```bash
python manage.py createsuperuser
```

### 7. Iniciar servidor

```bash
python manage.py runserver 8080
```

### 8. Acceder a la plataforma

- URL: `http://127.0.0.1:8080`
- Panel Admin: `http://127.0.0.1:8080/admin`

---

## 🗂️ Estructura del Proyecto

```
cyberquest/
├── core/                       # Aplicación principal
│   ├── templates/              # Templates HTML
│   │   ├── nav.html           # Sidebar navegación
│   │   ├── dashboard.html     # Panel principal
│   │   ├── user_list.html     # CRUD usuarios
│   │   ├── challenge_*.html   # Gestión de retos
│   │   ├── team_*.html        # Gestión de equipos
│   │   ├── module_*.html      # Cursos y lecciones
│   │   ├── event_*.html       # Eventos CTF
│   │   ├── ranking_*.html     # Rankings
│   │   ├── auditoria.html     # Logs del sistema
│   │   └── ai_assistant.html  # Chatbot IA
│   ├── models.py              # Modelos de base de datos
│   ├── views.py               # Vistas y lógica
│   ├── urls.py                # Rutas URL
│   ├── ia_ctf.py              # Lógica del asistente IA
│   ├── context_processors.py  # Variables globales
│   └── admin.py               # Panel administrativo
├── cyberquest/                # Configuración proyecto
│   ├── settings.py            # Configuración Django
│   └── urls.py                # URLs principales
├── media/                     # Archivos subidos (avatares)
├── dockerfiles/               # Dockerfiles para entornos
├── db.sqlite3                 # Base de datos
├── manage.py                  # Script de gestión
├── requirements.txt           # Dependencias
├── .env                       # Variables de entorno
└── README.md                  # Documentación
```

---

## 👥 Roles y Permisos

| Rol | Permisos |
|-----|----------|
| **Competidor** | Ver retos, resolver flags, unirse a equipos, ver rankings, usar IA, inscribirse a eventos |
| **Instructor** | Crear/editar retos, módulos, lecciones y eventos |
| **Administrador** | Gestionar usuarios, ver auditoría, activar/desactivar IA |

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 6.0.5** - Framework web
- **SQLite3** - Base de datos
- **Docker** - Entornos de laboratorio
- **OpenAI/Hugging Face** - API para asistente IA

### Frontend
- **HTML5 / CSS3** - Estructura y estilos
- **JavaScript** - Interactividad
- **Chart.js** - Gráficas estadísticas
- **FontAwesome** - Iconos
- **Google Fonts** - Tipografías (Orbitron, Share Tech Mono)

### Seguridad
- **python-dotenv** - Variables de entorno
- **CSRF Protection** - Protección Django
- **Password Hashing** - Encriptación de contraseñas

---

## 📝 Licencia

Desarrollado por **Yhonatan Leonardo Mamani Torrez**

Proyecto educativo - Todos los derechos reservados © 2025

---

## 📧 Contacto

- **Autor:** Yhonatan Leonardo Mamani Torrez
- **Email:** yonconortorez@gmail.com

---

## 🙏 Agradecimientos

- A la comunidad de ciberseguridad por la inspiración
- A Django por el excelente framework
- A Hugging Face por la API gratuita

---

**CyberQuest - Aprende, Compite y Conviértete en Experto en Ciberseguridad**