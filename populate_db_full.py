#!/usr/bin/env python
"""
Script para poblar la base de datos de CyberQuest con MUCHOS datos de prueba
Ejecutar: python populate_db_full.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberquest.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError
from core.models import (
    Perfil, Categoria, Reto, RecursoReto, IntentoReto,
    Equipo, Modulo, Leccion, Pregunta, Evento, 
    ConfiguracionIA, RegistroAuditoria
)


def crear_usuarios():
    """Crear usuarios: Admins, Instructores y Competidores"""
    print("\n👥 Creando usuarios...")
    
    usuarios_data = [
        # Administradores
        {"username": "admin", "email": "admin@cyberquest.com", "password": "admin123", "rol": "ADMIN", "puntos": 5000, "avatar": None},
        {"username": "superadmin", "email": "superadmin@cyberquest.com", "password": "super123", "rol": "ADMIN", "puntos": 10000, "avatar": None},
        
        # Instructores
        {"username": "instructor1", "email": "instructor1@cyberquest.com", "password": "instructor123", "rol": "INSTRUCTOR", "puntos": 2500, "avatar": None},
        {"username": "instructor2", "email": "instructor2@cyberquest.com", "password": "instructor456", "rol": "INSTRUCTOR", "puntos": 1800, "avatar": None},
        {"username": "instructor3", "email": "instructor3@cyberquest.com", "password": "instructor789", "rol": "INSTRUCTOR", "puntos": 3200, "avatar": None},
        {"username": "cyber_mentor", "email": "mentor@cyberquest.com", "password": "mentor123", "rol": "INSTRUCTOR", "puntos": 4500, "avatar": None},
        {"username": "security_pro", "email": "securitypro@cyberquest.com", "password": "pro123", "rol": "INSTRUCTOR", "puntos": 3800, "avatar": None},
        
        # Competidores (Estudiantes)
        {"username": "kali", "email": "kali@example.com", "password": "kali123", "rol": "ESTUDIANTE", "puntos": 850, "avatar": None},
        {"username": "neo", "email": "neo@matrix.com", "password": "neo123", "rol": "ESTUDIANTE", "puntos": 1250, "avatar": None},
        {"username": "trinity", "email": "trinity@matrix.com", "password": "trinity123", "rol": "ESTUDIANTE", "puntos": 920, "avatar": None},
        {"username": "morpheus", "email": "morpheus@matrix.com", "password": "morpheus123", "rol": "ESTUDIANTE", "puntos": 1100, "avatar": None},
        {"username": "oracle", "email": "oracle@matrix.com", "password": "oracle123", "rol": "ESTUDIANTE", "puntos": 780, "avatar": None},
        {"username": "switch", "email": "switch@matrix.com", "password": "switch123", "rol": "ESTUDIANTE", "puntos": 650, "avatar": None},
        {"username": "cypher", "email": "cypher@matrix.com", "password": "cypher123", "rol": "ESTUDIANTE", "puntos": 540, "avatar": None},
        {"username": "tank", "email": "tank@matrix.com", "password": "tank123", "rol": "ESTUDIANTE", "puntos": 430, "avatar": None},
        {"username": "dozer", "email": "dozer@matrix.com", "password": "dozer123", "rol": "ESTUDIANTE", "puntos": 390, "avatar": None},
        {"username": "apoc", "email": "apoc@matrix.com", "password": "apoc123", "rol": "ESTUDIANTE", "puntos": 310, "avatar": None},
        {"username": "mouse", "email": "mouse@matrix.com", "password": "mouse123", "rol": "ESTUDIANTE", "puntos": 280, "avatar": None},
        {"username": "seraph", "email": "seraph@matrix.com", "password": "seraph123", "rol": "ESTUDIANTE", "puntos": 670, "avatar": None},
        {"username": "baine", "email": "baine@matrix.com", "password": "baine123", "rol": "ESTUDIANTE", "puntos": 520, "avatar": None},
        {"username": "ghost", "email": "ghost@cyber.com", "password": "ghost123", "rol": "ESTUDIANTE", "puntos": 950, "avatar": None},
        {"username": "shadow", "email": "shadow@cyber.com", "password": "shadow123", "rol": "ESTUDIANTE", "puntos": 880, "avatar": None},
        {"username": "phoenix", "email": "phoenix@cyber.com", "password": "phoenix123", "rol": "ESTUDIANTE", "puntos": 760, "avatar": None},
        {"username": "raven", "email": "raven@cyber.com", "password": "raven123", "rol": "ESTUDIANTE", "puntos": 690, "avatar": None},
        {"username": "viper", "email": "viper@cyber.com", "password": "viper123", "rol": "ESTUDIANTE", "puntos": 610, "avatar": None},
        {"username": "falcon", "email": "falcon@cyber.com", "password": "falcon123", "rol": "ESTUDIANTE", "puntos": 580, "avatar": None},
        {"username": "eagle", "email": "eagle@cyber.com", "password": "eagle123", "rol": "ESTUDIANTE", "puntos": 550, "avatar": None},
        {"username": "wolf", "email": "wolf@cyber.com", "password": "wolf123", "rol": "ESTUDIANTE", "puntos": 490, "avatar": None},
        {"username": "tiger", "email": "tiger@cyber.com", "password": "tiger123", "rol": "ESTUDIANTE", "puntos": 470, "avatar": None},
        {"username": "lion", "email": "lion@cyber.com", "password": "lion123", "rol": "ESTUDIANTE", "puntos": 450, "avatar": None},
        {"username": "panther", "email": "panther@cyber.com", "password": "panther123", "rol": "ESTUDIANTE", "puntos": 420, "avatar": None},
        {"username": "jaguar", "email": "jaguar@cyber.com", "password": "jaguar123", "rol": "ESTUDIANTE", "puntos": 400, "avatar": None},
        {"username": "leopard", "email": "leopard@cyber.com", "password": "leopard123", "rol": "ESTUDIANTE", "puntos": 380, "avatar": None},
        {"username": "cheetah", "email": "cheetah@cyber.com", "password": "cheetah123", "rol": "ESTUDIANTE", "puntos": 360, "avatar": None},
        {"username": "lynx", "email": "lynx@cyber.com", "password": "lynx123", "rol": "ESTUDIANTE", "puntos": 340, "avatar": None},
        {"username": "caracal", "email": "caracal@cyber.com", "password": "caracal123", "rol": "ESTUDIANTE", "puntos": 320, "avatar": None},
        {"username": "serval", "email": "serval@cyber.com", "password": "serval123", "rol": "ESTUDIANTE", "puntos": 300, "avatar": None},
        {"username": "ocelot", "email": "ocelot@cyber.com", "password": "ocelot123", "rol": "ESTUDIANTE", "puntos": 290, "avatar": None},
        {"username": "margay", "email": "margay@cyber.com", "password": "margay123", "rol": "ESTUDIANTE", "puntos": 270, "avatar": None},
        {"username": "geoffroy", "email": "geoffroy@cyber.com", "password": "geoffroy123", "rol": "ESTUDIANTE", "puntos": 260, "avatar": None},
        {"username": "kodkod", "email": "kodkod@cyber.com", "password": "kodkod123", "rol": "ESTUDIANTE", "puntos": 250, "avatar": None},
    ]
    
    usuarios_creados = []
    for data in usuarios_data:
        try:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "is_staff": data["rol"] == "ADMIN",
                    "is_superuser": data["rol"] == "ADMIN"
                }
            )
            if created:
                user.set_password(data["password"])
                user.save()
                Perfil.objects.create(
                    usuario=user,
                    rol=data["rol"],
                    puntos=data["puntos"]
                )
                print(f"   ✅ Usuario creado: {data['username']} ({data['rol']}) - {data['puntos']} pts")
            else:
                print(f"   ⚠️ Usuario ya existe: {data['username']}")
            usuarios_creados.append(user)
        except IntegrityError:
            print(f"   ❌ Error al crear: {data['username']}")
    
    return usuarios_creados


def crear_equipos(usuarios):
    """Crear equipos y asignar miembros"""
    print("\n👥 Creando equipos...")
    
    estudiantes = [u for u in usuarios if u.perfil.rol == "ESTUDIANTE"]
    instructores = [u for u in usuarios if u.perfil.rol == "INSTRUCTOR"]
    
    equipos_data = [
        {"nombre": "Matrix Hackers", "descripcion": "Especialistas en vulnerabilidades web y cloud", "lider": "neo", "miembros": ["trinity", "morpheus", "oracle"]},
        {"nombre": "Red Team Elite", "descripcion": "Equipo de ataque especializado en pentesting", "lider": "kali", "miembros": ["ghost", "shadow", "phoenix", "raven"]},
        {"nombre": "Blue Team Defenders", "descripcion": "Defensores de la red, especialistas en forense", "lider": "trinity", "miembros": ["cypher", "tank", "dozer"]},
        {"nombre": "Cyber Wolves", "descripcion": "Expertos en OSINT y esteganografía", "lider": "wolf", "miembros": ["lynx", "tiger", "panther"]},
        {"nombre": "Phoenix Rising", "descripcion": "Equipo de élite en ciberseguridad", "lider": "phoenix", "miembros": ["eagle", "falcon", "raven"]},
        {"nombre": "Shadow Legion", "descripcion": "Especialistas en vulnerabilidades de día cero", "lider": "shadow", "miembros": ["viper", "seraph", "baine"]},
        {"nombre": "Cyber Guardians", "descripcion": "Protegiendo la red desde las sombras", "lider": "ghost", "miembros": ["apoc", "mouse", "switch"]},
        {"nombre": "Null Byte Crew", "descripcion": "Maestros en explotación de binarios", "lider": "cypher", "miembros": ["tank", "dozer", "apoc"]},
        {"nombre": "The Hackademy", "descripcion": "Equipo educativo para principiantes", "lider": "instructor1", "miembros": ["kali", "neo", "trinity"]},
        {"nombre": "Instructor Team", "descripcion": "Equipo de instructores de CyberQuest", "lider": "instructor2", "miembros": ["instructor3", "cyber_mentor", "security_pro"]},
    ]
    
    equipos_creados = []
    for data in equipos_data:
        lider = User.objects.get(username=data["lider"])
        equipo, created = Equipo.objects.get_or_create(
            nombre=data["nombre"],
            defaults={
                "descripcion": data["descripcion"],
                "lider": lider,
                "puntos": random.randint(500, 3000)
            }
        )
        if created:
            print(f"   ✅ Equipo creado: {data['nombre']}")
            for miembro_username in data.get("miembros", []):
                try:
                    miembro = User.objects.get(username=miembro_username)
                    equipo.miembros.add(miembro)
                except User.DoesNotExist:
                    pass
        equipos_creados.append(equipo)
    
    return equipos_creados


def crear_categorias():
    """Crear categorías de retos"""
    print("\n📁 Creando categorías...")
    categorias = [
        "🌐 Web", "🔐 Criptografía", "🕵️ Forense", 
        "💥 Pwn", "🔄 Reverse", "🔎 OSINT", "🖼️ Esteganografía",
        "☁️ Cloud", "📱 Mobile", "🔧 Miscelánea", "🧠 MQTT", "🛡️ ICS/SCADA"
    ]
    
    for cat in categorias:
        Categoria.objects.get_or_create(nombre=cat)
        print(f"   ✅ {cat}")
    return Categoria.objects.all()


def crear_retos():
    """Crear 70+ retos CTF"""
    print("\n🏆 Creando retos (70+ retos)...")
    categorias = list(Categoria.objects.all())
    instructor = User.objects.filter(perfil__rol="INSTRUCTOR").first()
    if not instructor:
        instructor = User.objects.first()
    
    retos_data = [
        # 🌐 WEB
        {"titulo": "SQL Injection 101", "descripcion": "Encuentra la vulnerabilidad SQL Injection en el formulario de login.", "dificultad": "PRINCIPIANTE", "puntos": 100, "bandera": "flag{sql_injection_basico}", "pista": "Prueba con ' OR '1'='1", "categoria": "🌐 Web"},
        {"titulo": "XSS Vulnerable", "descripcion": "El sitio web es vulnerable a XSS. Encuentra la bandera.", "dificultad": "PRINCIPIANTE", "puntos": 100, "bandera": "flag{xss_almacenado}", "pista": "Usa <script>alert(1)</script>", "categoria": "🌐 Web"},
        {"titulo": "JWT Forgery", "descripcion": "El token JWT puede ser manipulado.", "dificultad": "INTERMEDIO", "puntos": 200, "bandera": "flag{jwt_alg_none}", "pista": "Cambia el algoritmo a 'none'", "categoria": "🌐 Web"},
        {"titulo": "Path Traversal", "descripcion": "Lee el archivo /etc/passwd", "dificultad": "INTERMEDIO", "puntos": 150, "bandera": "flag{path_traversal}", "pista": "Usa ../../../etc/passwd", "categoria": "🌐 Web"},
        {"titulo": "Command Injection", "descripcion": "Ejecuta comandos en el servidor.", "dificultad": "AVANZADO", "puntos": 250, "bandera": "flag{cmd_injection}", "pista": "Usa ; ls -la", "categoria": "🌐 Web"},
        
        # 🔐 CRIPTOGRAFÍA
        {"titulo": "Descifrando Base64", "descripcion": "Decodifica el mensaje en Base64.", "dificultad": "PRINCIPIANTE", "puntos": 50, "bandera": "flag{base64_decode}", "pista": "Usa base64 -d", "categoria": "🔐 Criptografía"},
        {"titulo": "MD5 Crack", "descripcion": "Descifra el hash MD5: 5d41402abc4b2a76b9719d911017c592", "dificultad": "INTERMEDIO", "puntos": 150, "bandera": "flag{hello_md5}", "pista": "El hash es de 'hello'", "categoria": "🔐 Criptografía"},
        {"titulo": "Caesar Cipher", "descripcion": "Descifra: VQREHFXQH", "dificultad": "PRINCIPIANTE", "puntos": 50, "bandera": "flag{caesar_cipher}", "pista": "Rota 3", "categoria": "🔐 Criptografía"},
        {"titulo": "RSA Beginner", "descripcion": "Descifra: n=3233, e=17, c=855", "dificultad": "AVANZADO", "puntos": 300, "bandera": "flag{rsa_decrypt}", "pista": "p=61, q=53", "categoria": "🔐 Criptografía"},
        
        # 🕵️ FORENSE
        {"titulo": "Análisis de PCAP", "descripcion": "Analiza el archivo .pcap", "dificultad": "INTERMEDIO", "puntos": 200, "bandera": "flag{pcap_analysis}", "pista": "Filtra por HTTP", "categoria": "🕵️ Forense"},
        {"titulo": "Metadata Analysis", "descripcion": "Encuentra la bandera en los metadatos.", "dificultad": "PRINCIPIANTE", "puntos": 100, "bandera": "flag{exif_metadata}", "pista": "Usa exiftool", "categoria": "🕵️ Forense"},
        {"titulo": "Memory Forensics", "descripcion": "Analiza el volcado de memoria.", "dificultad": "AVANZADO", "puntos": 350, "bandera": "flag{memory_forensics}", "pista": "Usa volatility", "categoria": "🕵️ Forense"},
        
        # 💥 PWN
        {"titulo": "Buffer Overflow", "descripcion": "Explota el buffer overflow.", "dificultad": "AVANZADO", "puntos": 300, "bandera": "flag{bof_exploit}", "pista": "Sobrescribe la dirección de retorno", "categoria": "💥 Pwn"},
        {"titulo": "Format String", "descripcion": "Explota format string.", "dificultad": "AVANZADO", "puntos": 300, "bandera": "flag{format_string}", "pista": "Usa %p y %n", "categoria": "💥 Pwn"},
        
        # 🔄 REVERSE
        {"titulo": "Ingeniería Reversa Básica", "descripcion": "Realiza ingeniería inversa.", "dificultad": "INTERMEDIO", "puntos": 200, "bandera": "flag{reverse_101}", "pista": "Usa Ghidra", "categoria": "🔄 Reverse"},
        {"titulo": "Crackme 1", "descripcion": "Encuentra la contraseña.", "dificultad": "PRINCIPIANTE", "puntos": 100, "bandera": "flag{crackme_1}", "pista": "Analiza la función main", "categoria": "🔄 Reverse"},
        
        # 🖼️ ESTEGANOGRAFÍA
        {"titulo": "Steghide Basic", "descripcion": "Extrae el mensaje oculto.", "dificultad": "PRINCIPIANTE", "puntos": 100, "bandera": "flag{steghide_basic}", "pista": "Usa steghide", "categoria": "🖼️ Esteganografía"},
        {"titulo": "QR Code", "descripcion": "Decodifica el código QR.", "dificultad": "PRINCIPIANTE", "puntos": 50, "bandera": "flag{qr_decode}", "pista": "Escanea el QR", "categoria": "🖼️ Esteganografía"},
        
        # 🔎 OSINT
        {"titulo": "Social Media", "descripcion": "Investiga al hacker 'CyberGhost'.", "dificultad": "INTERMEDIO", "puntos": 150, "bandera": "flag{osint_social}", "pista": "Busca en Twitter y GitHub", "categoria": "🔎 OSINT"},
        {"titulo": "DNS Recon", "descripcion": "Realiza reconocimiento DNS.", "dificultad": "PRINCIPIANTE", "puntos": 100, "bandera": "flag{dns_recon}", "pista": "Usa dig y nslookup", "categoria": "🔎 OSINT"},
    ]
    
    # Duplicar para tener más retos
    for i in range(3):
        for data in retos_data[:]:
            new_data = data.copy()
            new_data["titulo"] = f"{data['titulo']} {i+2}"
            new_data["bandera"] = data["bandera"].replace("}", f"_{i+2}}")
            retos_data.append(new_data)
    
    retos_creados = []
    for data in retos_data[:70]:  # Limitar a 70 retos
        categoria = Categoria.objects.get(nombre=data["categoria"])
        reto, created = Reto.objects.get_or_create(
            titulo=data["titulo"],
            defaults={
                "descripcion": data["descripcion"],
                "categoria": categoria,
                "dificultad": data["dificultad"],
                "puntos": data["puntos"],
                "bandera": data["bandera"],
                "pista": data["pista"],
                "esta_oculto": False,
                "creado_por": instructor
            }
        )
        if created:
            print(f"   ✅ {data['titulo']}")
        retos_creados.append(reto)
    
    return retos_creados


def crear_modulos():
    """Crear módulos de aprendizaje"""
    print("\n📚 Creando módulos...")
    instructor = User.objects.filter(perfil__rol="INSTRUCTOR").first()
    
    modulos_data = [
        {"titulo": "Fundamentos de Ciberseguridad", "descripcion": "Conceptos básicos", "lecciones": 3},
        {"titulo": "Hacking Ético", "descripcion": "Metodologías y técnicas", "lecciones": 3},
        {"titulo": "CTF para Principiantes", "descripcion": "Aprende a resolver CTFs", "lecciones": 3},
        {"titulo": "Web Security", "descripcion": "Vulnerabilidades web", "lecciones": 4},
        {"titulo": "Criptografía Avanzada", "descripcion": "Cifrados modernos", "lecciones": 3},
        {"titulo": "Forense Digital", "descripcion": "Análisis forense", "lecciones": 3},
        {"titulo": "Reverse Engineering", "descripcion": "Ingeniería inversa", "lecciones": 3},
        {"titulo": "Cloud Security", "descripcion": "Seguridad en la nube", "lecciones": 3},
        {"titulo": "OSINT", "descripcion": "Inteligencia de fuentes abiertas", "lecciones": 3},
        {"titulo": "Esteganografía", "descripcion": "Ocultamiento de información", "lecciones": 2},
    ]
    
    modulos = []
    for data in modulos_data:
        modulo, created = Modulo.objects.get_or_create(
            titulo=data["titulo"],
            defaults={
                "descripcion": data["descripcion"],
                "creado_por": instructor,
                "esta_publicado": True
            }
        )
        if created:
            print(f"   ✅ {data['titulo']}")
            
            for i in range(data["lecciones"]):
                Leccion.objects.get_or_create(
                    modulo=modulo,
                    titulo=f"Lección {i+1}: {data['titulo']}",
                    defaults={
                        "contenido": f"Contenido de la lección {i+1} del módulo {data['titulo']}. Aquí aprenderás los fundamentos básicos.",
                        "orden": i+1
                    }
                )
        modulos.append(modulo)
    
    return modulos


def crear_eventos():
    """Crear eventos CTF"""
    print("\n🎯 Creando eventos...")
    ahora = timezone.now()
    instructor = User.objects.filter(perfil__rol="INSTRUCTOR").first()
    retos = list(Reto.objects.all())
    
    eventos_data = [
        {"nombre": "CyberQuest CTF 2025", "descripcion": "Evento principal anual", "dias_inicio": 7, "duracion_dias": 3, "activo": False},
        {"nombre": "Hacking Challenge", "descripcion": "Desafío de 48 horas", "dias_inicio": -2, "duracion_dias": 4, "activo": True},
        {"nombre": "Web Security CTF", "descripcion": "Especializado en web", "dias_inicio": 14, "duracion_dias": 2, "activo": False},
        {"nombre": "Crypto Challenge", "descripcion": "Desafíos de criptografía", "dias_inicio": 21, "duracion_dias": 3, "activo": False},
        {"nombre": "Forense Weekend", "descripcion": "Fin de semana forense", "dias_inicio": 30, "duracion_dias": 2, "activo": False},
        {"nombre": "Pwn Academy", "descripcion": "Explotación de binarios", "dias_inicio": 45, "duracion_dias": 5, "activo": False},
    ]
    
    eventos = []
    for data in eventos_data:
        fecha_inicio = ahora + timedelta(days=data["dias_inicio"])
        fecha_fin = fecha_inicio + timedelta(days=data["duracion_dias"])
        
        evento, created = Evento.objects.get_or_create(
            nombre=data["nombre"],
            defaults={
                "descripcion": data["descripcion"],
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "esta_activo": data["activo"],
                "reglas": f"Reglas del evento {data['nombre']}",
                "creado_por": instructor
            }
        )
        if created:
            for reto in random.sample(retos, min(3, len(retos))):
                evento.retos.add(reto)
            print(f"   ✅ {data['nombre']}")
        eventos.append(evento)
    
    return eventos


def crear_intentos(usuarios, retos):
    """Crear intentos de retos resueltos"""
    print("\n🎮 Creando intentos de retos...")
    contador = 0
    
    for usuario in usuarios[:20]:  # 20 usuarios tendrán intentos
        if usuario.perfil.rol == "ESTUDIANTE":
            for reto in random.sample(retos, min(random.randint(3, 10), len(retos))):
                try:
                    IntentoReto.objects.get_or_create(
                        usuario=usuario,
                        reto=reto,
                        defaults={
                            "bandera_enviada": reto.bandera,
                            "es_correcto": True
                        }
                    )
                    usuario.perfil.puntos += reto.puntos
                    usuario.perfil.save()
                    contador += 1
                except:
                    pass
    
    print(f"   ✅ {contador} intentos creados")


def crear_configuracion():
    """Crear configuración inicial"""
    print("\n⚙️ Creando configuración...")
    config, created = ConfiguracionIA.objects.get_or_create(
        defaults={
            "asistente_activo": True,
            "limite_consultas_por_dia": 10
        }
    )
    if created:
        print("   ✅ Configuración IA creada")


def main():
    print("=" * 60)
    print("🚀 CyberQuest - Población FULL de Base de Datos")
    print("=" * 60)
    
    # Ejecutar todas las funciones
    crear_usuarios()
    crear_categorias()
    retos = crear_retos()
    modulos = crear_modulos()
    eventos = crear_eventos()
    
    usuarios = User.objects.all()
    crear_equipos(usuarios)
    crear_intentos(usuarios, retos)
    crear_configuracion()
    
    print("\n" + "=" * 60)
    print("✅ BASE DE DATOS POBLADA EXITOSAMENTE!")
    print("=" * 60)
    print(f"\n📊 RESUMEN FINAL:")
    print(f"   👥 Usuarios: {User.objects.count()} (2 Admin, 5 Instructores, {User.objects.filter(perfil__rol='ESTUDIANTE').count()} Competidores)")
    print(f"   🏆 Retos: {Reto.objects.count()}")
    print(f"   📚 Módulos: {Modulo.objects.count()}")
    print(f"   🎯 Eventos: {Evento.objects.count()}")
    print(f"   👥 Equipos: {Equipo.objects.count()}")
    print(f"   🎮 Intentos: {IntentoReto.objects.count()}")
    
    print("\n🔑 CREDENCIALES DE ACCESO:")
    print("   👑 Admin: admin / admin123")
    print("   👑 SuperAdmin: superadmin / super123")
    print("   📚 Instructor: instructor1 / instructor123")
    print("   🎓 Competidor: kali / kali123")
    print("   🎓 Competidor: neo / neo123")
    print("   🎓 Competidor: trinity / trinity123")


if __name__ == "__main__":
    main()  