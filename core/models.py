from django.db import models
from django.contrib.auth.models import User
import uuid

# ============================================================
# MÓDULO 1: ADMINISTRACIÓN DE USUARIOS
# ============================================================

class Perfil(models.Model):
    ROLES = [
        ('ESTUDIANTE', 'Competidor'),
        ('INSTRUCTOR', 'Instructor'),
        ('ADMIN', 'Administrador'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, default='ESTUDIANTE')
    puntos = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    esta_bloqueado = models.BooleanField(default=False)
    
    def __str__(self):
        return self.usuario.username


class RestablecerContrasena(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.token[:20]}"


# ============================================================
# MÓDULO 2: GESTIÓN DE EQUIPOS
# ============================================================

class Equipo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    lider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipos_liderados')
    miembros = models.ManyToManyField(User, related_name='equipos')
    codigo_invitacion = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    creado_en = models.DateTimeField(auto_now_add=True)
    puntos = models.IntegerField(default=0)
    
    def __str__(self):
        return self.nombre
    
    @property  # <-- IMPORTANTE: esto hace que funcione como campo en templates
    def cantidad_miembros(self):
        return self.miembros.count() + 1


class InvitacionEquipo(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADA', 'Aceptada'),
        ('RECHAZADA', 'Rechazada')
    ]
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    usuario_invitado = models.ForeignKey(User, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    creado_en = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.equipo.nombre} -> {self.usuario_invitado.username}"


# ============================================================
# MÓDULO 3: FORMACIÓN Y APRENDIZAJE
# ============================================================

class Modulo(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    creado_en = models.DateTimeField(auto_now_add=True)
    esta_publicado = models.BooleanField(default=True)
    
    def __str__(self):
        return self.titulo


class Leccion(models.Model):
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name='lecciones')
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    orden = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.modulo.titulo} - {self.titulo}"


class Recurso(models.Model):
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE, related_name='recursos')
    titulo = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='recursos/', blank=True, null=True)
    enlace = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.titulo


class Pregunta(models.Model):
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE, related_name='preguntas')
    texto_pregunta = models.TextField()
    respuesta_correcta = models.CharField(max_length=500)
    puntos = models.IntegerField(default=10)
    
    def __str__(self):
        return self.texto_pregunta[:50]


class ProgresoUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE)
    completado = models.BooleanField(default=False)
    puntaje = models.IntegerField(default=0)
    completado_en = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['usuario', 'leccion']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.leccion.titulo} - {'Completado' if self.completado else 'Pendiente'}"


class Certificado(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    emitido_en = models.DateTimeField(auto_now_add=True)
    codigo = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.modulo.titulo}"


# ============================================================
# MÓDULO 4: GESTIÓN DE RETOS CTF
# ============================================================

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre


class Reto(models.Model):
    DIFICULTADES = [
        ('PRINCIPIANTE', 'Principiante'),
        ('INTERMEDIO', 'Intermedio'),
        ('AVANZADO', 'Avanzado')
    ]
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    dificultad = models.CharField(max_length=20, choices=DIFICULTADES, default='PRINCIPIANTE')
    puntos = models.IntegerField(default=100)
    bandera = models.CharField(max_length=200)
    pista = models.TextField(blank=True, null=True)
    solucion = models.TextField(blank=True, null=True)
    esta_oculto = models.BooleanField(default=False)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    creado_en = models.DateTimeField(auto_now_add=True)
    tiene_docker = models.BooleanField(default=False)
    docker_image = models.CharField(max_length=200, blank=True, null=True)
    docker_ports = models.CharField(max_length=100, blank=True, null=True)
    docker_command = models.CharField(max_length=200, blank=True, null=True)
    dockerfile = models.TextField(blank=True, null=True)
    docker_image_name = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return self.titulo


class RecursoReto(models.Model):
    reto = models.ForeignKey(Reto, on_delete=models.CASCADE, related_name='recursos')
    titulo = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='retos/', blank=True, null=True)
    
    def __str__(self):
        return self.titulo


class IntentoReto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    reto = models.ForeignKey(Reto, on_delete=models.CASCADE)
    bandera_enviada = models.CharField(max_length=200)
    es_correcto = models.BooleanField(default=False)
    intentado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['usuario', 'reto']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.reto.titulo} - {'Correcto' if self.es_correcto else 'Incorrecto'}"





# ============================================================
# MÓDULO 5: CONTROL DE ENTORNOS
# ============================================================

class Entorno(models.Model):
    ESTADOS = [
        ('DETENIDO', 'Detenido'),
        ('EJECUTANDO', 'Ejecutando'),
        ('ERROR', 'Error')
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    reto = models.ForeignKey(Reto, on_delete=models.CASCADE)
    id_contenedor = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='DETENIDO')
    iniciado_en = models.DateTimeField(null=True, blank=True)
    configuracion_vpn = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.reto.titulo} - {self.estado}"


# ============================================================
# MÓDULO 6: EVALUACIÓN DE RESULTADOS
# ============================================================

class EnvioBandera(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    reto = models.ForeignKey(Reto, on_delete=models.CASCADE)
    bandera = models.CharField(max_length=200)
    es_correcto = models.BooleanField(default=False)
    enviado_en = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.reto.titulo} - {'Correcto' if self.es_correcto else 'Incorrecto'}"





# ============================================================
# MÓDULO 7: CLASIFICACIÓN Y RANKING
# (No necesita modelos extras, usa Perfil.puntos y Equipo.puntos)
# ============================================================


# ============================================================
# MÓDULO 8: AUDITORÍA Y MONITOREO
# ============================================================

class RegistroAuditoria(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    direccion_ip = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.accion} - {self.timestamp}"


# ============================================================
# MÓDULO 9: ASISTENTE IA
# ============================================================

class ConsultaIA(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    pregunta = models.TextField()
    respuesta = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.pregunta[:50]}"




class ConfiguracionIA(models.Model):
    asistente_activo = models.BooleanField(default=True)
    limite_consultas_por_dia = models.IntegerField(default=10)
    actualizado_en = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"IA Activa: {self.asistente_activo}"


# ============================================================
# MÓDULO 10: EVENTOS CTF
# ============================================================

class Evento(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    esta_activo = models.BooleanField(default=False)
    retos = models.ManyToManyField(Reto, related_name='eventos')
    participantes = models.ManyToManyField(User, related_name='eventos', blank=True)
    reglas = models.TextField(blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='eventos_creados')  
    def __str__(self):
        return self.nombre
    
    def esta_inscrito(self, usuario):
        return self.participantes.filter(id=usuario.id).exists()



