#!/usr/bin/env python
import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberquest.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import (
    Perfil, Categoria, Reto, RecursoReto, IntentoReto,
    Equipo, Modulo, Leccion, Pregunta, ProgresoUsuario,
    Evento, ConsultaIA, ConfiguracionIA, RegistroAuditoria
)

def clear_database():
    """Limpiar datos existentes"""
    print("🗑️  Limpiando datos existentes...")
    models = [IntentoReto, ProgresoUsuario, ConsultaIA, RegistroAuditoria,
              Pregunta, Leccion, Modulo, Evento, Equipo, Reto, Perfil, User]
    for model in models:
        try:
            model.objects.all().delete()
            print(f"  ✅ {model.__name__} limpiado")
        except:
            pass
    print("✅ Datos existentes eliminados\n")

def create_users():
    """Crear usuarios y perfiles"""
    print("👥 Creando usuarios...")
    users_data = [
        ('admin', 'admin@cyberquest.com', 'admin123', 'ADMIN'),
        ('instructor1', 'instructor1@cyberquest.com', 'instructor123', 'INSTRUCTOR'),
        ('instructor2', 'instructor2@cyberquest.com', 'instructor123', 'INSTRUCTOR'),
        ('kali', 'kali@cyberquest.com', 'kali123', 'ESTUDIANTE'),
        ('neo', 'neo@cyberquest.com', 'neo123', 'ESTUDIANTE'),
        ('trinity', 'trinity@cyberquest.com', 'trinity123', 'ESTUDIANTE'),
        ('morpheus', 'morpheus@cyberquest.com', 'morpheus123', 'ESTUDIANTE'),
        ('cypher', 'cypher@cyberquest.com', 'cypher123', 'ESTUDIANTE'),
        ('oracle', 'oracle@cyberquest.com', 'oracle123', 'ESTUDIANTE'),
        ('smith', 'smith@cyberquest.com', 'smith123', 'ESTUDIANTE'),
    ]
    
    users = []
    for username, email, password, rol in users_data:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )
        if created:
            user.set_password(password)
            user.save()
        
        perfil, _ = Perfil.objects.get_or_create(
            usuario=user,
            defaults={
                'rol': rol,
                'puntos': random.randint(0, 1500),
                'telefono': f'6{random.randint(10000000, 99999999)}',
                'esta_bloqueado': False
            }
        )
        users.append(user)
        print(f"  ✅ {username} ({rol}) - {perfil.puntos} pts")
    
    print(f"✅ {len(users)} usuarios creados\n")
    return users

def create_categorias():
    """Crear categorías de retos"""
    print("📂 Creando categorías...")
    categorias_data = [
        'Web Exploitation', 'Cryptography', 'Forensics', 
        'Pwn / Binary Exploitation', 'Reverse Engineering', 
        'OSINT', 'Steganography', 'Networking', 'Mobile Security', 'Cloud Security'
    ]
    
    categorias = []
    for nombre in categorias_data:
        cat, _ = Categoria.objects.get_or_create(nombre=nombre)
        categorias.append(cat)
        print(f"  ✅ {nombre}")
    
    print(f"✅ {len(categorias)} categorías creadas\n")
    return categorias

def create_retos(categorias, usuarios):
    """Crear retos CTF"""
    print("🎯 Creando retos...")
    
    retos_data = [
        # Retos Web
        ('SQL Injection 101', 'Encuentra la bandera en la base de datos vulnerable', 'PRINCIPIANTE', 100, 'flag{sql_injection_master}'),
        ('XSS Challenge', 'El sitio web es vulnerable a XSS', 'PRINCIPIANTE', 100, 'flag{xss_vulnerable}'),
        ('Command Injection', 'Ejecuta comandos en el servidor', 'INTERMEDIO', 200, 'flag{cmd_injection}'),
        ('JWT Attack', 'Explota la vulnerabilidad en JWT', 'AVANZADO', 300, 'flag{jwt_hacked}'),
        
        # Retos Criptografía
        ('Caesar Cipher', 'Descifra el mensaje cifrado con César', 'PRINCIPIANTE', 100, 'flag{caesar_cipher}'),
        ('RSA Basics', 'Rompe el cifrado RSA básico', 'INTERMEDIO', 200, 'flag{rsa_cracked}'),
        ('AES Encryption', 'Encuentra la clave AES', 'AVANZADO', 300, 'flag{aes_decrypted}'),
        
        # Retos Forense
        ('Hidden Metadata', 'Encuentra información oculta en la metadata', 'PRINCIPIANTE', 100, 'flag{metadata_found}'),
        ('PCAP Analysis', 'Analiza el tráfico de red', 'INTERMEDIO', 200, 'flag{pcap_master}'),
        ('Memory Dump', 'Investiga el volcado de memoria', 'AVANZADO', 300, 'flag{memory_analysis}'),
        
        # Retos Pwn
        ('Buffer Overflow', 'Explota el desbordamiento de buffer', 'INTERMEDIO', 250, 'flag{buffer_overflow}'),
        ('Format String', 'Aprovecha la vulnerabilidad de format string', 'AVANZADO', 350, 'flag{format_string}'),
        
        # Retos Reverse
        ('Keygen Me', 'Crea un keygen para este programa', 'INTERMEDIO', 200, 'flag{keygen_me}'),
        ('Crack Me', 'Ingeniería inversa básica', 'AVANZADO', 300, 'flag{crack_me}'),
    ]
    
    retos = []
    instructor = next(u for u in usuarios if u.perfil.rol == 'INSTRUCTOR')
    
    for i, (titulo, desc, dificultad, puntos, bandera) in enumerate(retos_data):
        categoria = categorias[i % len(categorias)]
        reto = Reto.objects.create(
            titulo=titulo,
            descripcion=desc,
            categoria=categoria,
            dificultad=dificultad,
            puntos=puntos,
            bandera=bandera,
            pista=f"Pista para {titulo}: Revisa bien los detalles",
            creado_por=instructor,
            esta_oculto=False
        )
        retos.append(reto)
        print(f"  ✅ {titulo} - {puntos} pts ({dificultad})")
    
    print(f"✅ {len(retos)} retos creados\n")
    return retos

def create_modulos():
    """Crear módulos de aprendizaje"""
    print("📚 Creando módulos de aprendizaje...")
    
    instructor = User.objects.get(username='instructor1')
    
    modulos_data = [
        ('Fundamentos de Ciberseguridad', 'Conceptos básicos de seguridad informática'),
        ('Hacking Ético', 'Metodologías y técnicas de pentesting'),
        ('Criptografía Avanzada', 'Algoritmos criptográficos modernos'),
        ('Análisis Forense Digital', 'Investigación de incidentes'),
        ('Desarrollo Seguro', 'Buenas prácticas en desarrollo de software'),
    ]
    
    modulos = []
    for titulo, desc in modulos_data:
        modulo = Modulo.objects.create(
            titulo=titulo,
            descripcion=desc,
            creado_por=instructor,
            esta_publicado=True
        )
        
        # Crear lecciones
        for i in range(1, 4):
            leccion = Leccion.objects.create(
                modulo=modulo,
                titulo=f"Lección {i}: {titulo[:20]} - Parte {i}",
                contenido=f"Contenido detallado de la lección {i} del módulo {titulo}.\n\nAquí se explican los conceptos fundamentales con ejemplos prácticos.\n\nCódigo de ejemplo:\n```python\nprint('Hola mundo')\n```",
                orden=i
            )
            
            # Crear preguntas
            Pregunta.objects.create(
                leccion=leccion,
                texto_pregunta=f"¿Cuál es el concepto principal de la lección {i}?",
                respuesta_correcta="Respuesta correcta ejemplo",
                puntos=10
            )
        
        modulos.append(modulo)
        print(f"  ✅ {titulo} - {modulo.lecciones.count()} lecciones")
    
    print(f"✅ {len(modulos)} módulos creados\n")
    return modulos

def create_equipos(usuarios):
    """Crear equipos"""
    print("👥 Creando equipos...")
    
    estudiantes = [u for u in usuarios if u.perfil.rol == 'ESTUDIANTE']
    
    equipos_data = [
        ('Los Hackers', 'Equipo de hacking ético'),
        ('Cyber Warriors', 'Defensores del ciberespacio'),
        ('Null Byte', 'Especialistas en exploits'),
        ('Root Access', 'Los mejores del CTF'),
    ]
    
    equipos = []
    for i, (nombre, desc) in enumerate(equipos_data):
        if i < len(estudiantes):
            lider = estudiantes[i]
            equipo = Equipo.objects.create(
                nombre=nombre,
                descripcion=desc,
                lider=lider,
                puntos=random.randint(500, 2000)
            )
            # Agregar miembros
            for j in range(1, 3):
                if i + j < len(estudiantes):
                    equipo.miembros.add(estudiantes[i + j])
            equipos.append(equipo)
            print(f"  ✅ {nombre} - Líder: {lider.username} - {equipo.miembros.count()} miembros")
    
    print(f"✅ {len(equipos)} equipos creados\n")
    return equipos

def create_intentos(usuarios, retos):
    """Crear intentos de retos"""
    print("🎯 Creando intentos de retos...")
    
    estudiantes = [u for u in usuarios if u.perfil.rol == 'ESTUDIANTE']
    intentos_count = 0
    
    for estudiante in estudiantes:
        # Cada estudiante resuelve algunos retos
        retos_resueltos = random.sample(retos, random.randint(1, len(retos) // 2))
        for reto in retos_resueltos:
            IntentoReto.objects.create(
                usuario=estudiante,
                reto=reto,
                bandera_enviada=reto.bandera,
                es_correcto=True
            )
            estudiante.perfil.puntos += reto.puntos
            estudiante.perfil.save()
            intentos_count += 1
    
    print(f"✅ {intentos_count} intentos correctos registrados\n")

def create_eventos(retos):
    """Crear eventos CTF"""
    print("🎪 Creando eventos...")
    
    instructor = User.objects.get(username='instructor1')
    ahora = timezone.now()
    
    eventos_data = [
        ('CTF EMI 2026', 'Competencia anual de la Escuela Militar de Ingeniería', 30, 60),
        ('CyberChallenge Week', 'Semana de desafíos intensivos', 7, 14),
        ('Hacking Night', 'Competencia nocturna de hacking', 1, 2),
        ('Crypto Masters', 'Especializado en criptografía', 14, 21),
    ]
    
    eventos = []
    for nombre, desc, dias_inicio, dias_fin in eventos_data:
        evento = Evento.objects.create(
            nombre=nombre,
            descripcion=desc,
            fecha_inicio=ahora + timedelta(days=dias_inicio),
            fecha_fin=ahora + timedelta(days=dias_fin),
            esta_activo=False,
            creado_por=instructor,
            reglas="1. No compartir flags\n2. No hacer trampa\n3. Divertirse"
        )
        # Agregar retos aleatorios
        for reto in random.sample(retos, random.randint(5, 10)):
            evento.retos.add(reto)
        eventos.append(evento)
        print(f"  ✅ {nombre} - {evento.retos.count()} retos")
    
    print(f"✅ {len(eventos)} eventos creados\n")
    return eventos

def create_consultas_ia(usuarios):
    """Crear historial de consultas IA"""
    print("🤖 Creando consultas al asistente IA...")
    
    estudiantes = [u for u in usuarios if u.perfil.rol == 'ESTUDIANTE']
    consultas_count = 0
    
    preguntas_respuestas = [
        ('¿Cuántos puntos tengo?', 'Tienes {puntos} puntos. ¡Sigue así!'),
        ('¿Cómo resuelvo un reto de SQL injection?', 'Prueba con comillas simples y UNION SELECT'),
        ('¿Qué es un buffer overflow?', 'Es cuando escribes más datos de los que el buffer puede contener'),
        ('¿Cómo funciona RSA?', 'RSA usa claves públicas y privadas basadas en números primos grandes'),
        ('Dame una pista para el reto Web', 'Revisa el código fuente y los parámetros GET/POST'),
    ]
    
    for estudiante in estudiantes:
        for _ in range(random.randint(1, 5)):
            pregunta, respuesta_base = random.choice(preguntas_respuestas)
            respuesta = respuesta_base.format(puntos=estudiante.perfil.puntos)
            ConsultaIA.objects.create(
                usuario=estudiante,
                pregunta=pregunta,
                respuesta=respuesta
            )
            consultas_count += 1
    
    print(f"✅ {consultas_count} consultas IA creadas\n")

def create_auditoria(usuarios):
    """Crear registros de auditoría"""
    print("📝 Creando registros de auditoría...")
    
    acciones = ['INICIAR_SESION', 'CERRAR_SESION', 'RESOLVER_RETO', 'CREAR_EQUIPO', 'UNIRSE_EQUIPO']
    auditoria_count = 0
    
    for usuario in usuarios:
        for _ in range(random.randint(3, 10)):
            accion = random.choice(acciones)
            RegistroAuditoria.objects.create(
                usuario=usuario,
                accion=accion,
                direccion_ip=f"192.168.1.{random.randint(1, 255)}"
            )
            auditoria_count += 1
    
    print(f"✅ {auditoria_count} registros de auditoría creados\n")

def configure_ia():
    """Configurar asistente IA"""
    print("⚙️ Configurando asistente IA...")
    
    config, _ = ConfiguracionIA.objects.get_or_create(
        id=1,
        defaults={'asistente_activo': True}
    )
    config.asistente_activo = True
    config.save()
    
    print(f"✅ Asistente IA {'activado' if config.asistente_activo else 'desactivado'}\n")

def main():
    print("=" * 60)
    print("🚀 CYBERQUEST - POBLANDO BASE DE DATOS")
    print("=" * 60 + "\n")
    
    clear_database()
    configure_ia()
    usuarios = create_users()
    categorias = create_categorias()
    retos = create_retos(categorias, usuarios)
    modulos = create_modulos()
    equipos = create_equipos(usuarios)
    create_intentos(usuarios, retos)
    eventos = create_eventos(retos)
    create_consultas_ia(usuarios)
    create_auditoria(usuarios)
    
    print("=" * 60)
    print("📊 ESTADÍSTICAS FINALES")
    print("=" * 60)
    print(f"👥 Usuarios: {User.objects.count()}")
    print(f"📂 Categorías: {Categoria.objects.count()}")
    print(f"🎯 Retos: {Reto.objects.count()}")
    print(f"📚 Módulos: {Modulo.objects.count()}")
    print(f"📖 Lecciones: {Leccion.objects.count()}")
    print(f"❓ Preguntas: {Pregunta.objects.count()}")
    print(f"👥 Equipos: {Equipo.objects.count()}")
    print(f"🏆 Intentos correctos: {IntentoReto.objects.filter(es_correcto=True).count()}")
    print(f"🎪 Eventos: {Evento.objects.count()}")
    print(f"🤖 Consultas IA: {ConsultaIA.objects.count()}")
    print(f"📝 Auditoría: {RegistroAuditoria.objects.count()}")
    print("=" * 60)
    print("✅ ¡Base de datos poblada exitosamente!")
    print("=" * 60)

if __name__ == "__main__":
    main()
