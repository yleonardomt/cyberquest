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

def crear_usuarios_especificos():
    """Crear usuarios específicos"""
    print(" Creando usuarios especificos...")
    
    usuarios_data = [
        ('adm', 'adm@cyberquest.com', 'adm', 'ADMIN'),
        ('inst', 'inst@cyberquest.com', 'inst', 'INSTRUCTOR'),
        ('leo', 'leo@cyberquest.com', 'leo', 'ESTUDIANTE'),
    ]
    
    usuarios = []
    for username, email, password, rol in usuarios_data:
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
                'puntos': 0,
                'telefono': f'6{random.randint(10000000, 99999999)}',
                'esta_bloqueado': False
            }
        )
        usuarios.append(user)
        print(f"  OK {username} ({rol}) creado - Pass: {password}")
    
    print(f"OK {len(usuarios)} usuarios creados\n")
    return usuarios

def crear_categorias():
    """Crear categorías de retos"""
    print(" Creando categorias...")
    categorias_data = [
        'Web Exploitation', 'Cryptography', 'Forensics', 
        'Pwn / Binary Exploitation', 'Reverse Engineering', 
        'OSINT', 'Steganography', 'Networking', 'Mobile Security', 
        'Cloud Security', 'Blockchain', 'IoT Security'
    ]
    
    categorias = []
    for nombre in categorias_data:
        cat, _ = Categoria.objects.get_or_create(nombre=nombre)
        categorias.append(cat)
        print(f"  OK {nombre}")
    
    print(f"OK {len(categorias)} categorias creadas\n")
    return categorias

def crear_modulos_con_preguntas():
    """Crear módulos con preguntas (respuesta = .)"""
    print(" Creando modulos con preguntas...")
    
    instructor = User.objects.get(username='inst')
    
    modulos_data = [
        ('Fundamentos de Ciberseguridad', 
         'Aprende los conceptos basicos de la seguridad informatica.',
         [
             ('Cual es el principio fundamental de la confidencialidad?', 10),
             ('Que significa la letra "I" en la triada CIA?', 10),
             ('Que tipo de ataque consiste en enviar datos maliciosos a una aplicacion web?', 15),
         ]),
        ('Hacking Etico y Pentesting', 
         'Metodologias y tecnicas profesionales de pruebas de penetracion.',
         [
             ('Que fase del pentesting consiste en recopilar informacion?', 10),
             ('Que herramienta se usa para escanear puertos?', 10),
             ('Que significa la sigla OWASP?', 15),
         ]),
        ('Criptografia Moderna', 
         'Algoritmos criptograficos y su aplicacion en la seguridad actual.',
         [
             ('Que tipo de cifrado usa la misma clave para cifrar y descifrar?', 10),
             ('Que algoritmo de cifrado asimetrico es el mas conocido?', 10),
             ('Que funcion se usa para generar hashes de contrasenas?', 15),
         ]),
    ]
    
    modulos = []
    for titulo, descripcion, preguntas_data in modulos_data:
        modulo = Modulo.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            creado_por=instructor,
            esta_publicado=True
        )
        
        # Crear 3 lecciones por modulo
        for i in range(1, 4):
            leccion = Leccion.objects.create(
                modulo=modulo,
                titulo=f"{titulo} - Leccion {i}",
                contenido=f"Contenido de la leccion {i} del modulo {titulo}",
                orden=i
            )
            
            # Agregar preguntas a la primera leccion de cada modulo
            if i == 1:
                for pregunta_texto, puntos in preguntas_data:
                    Pregunta.objects.create(
                        leccion=leccion,
                        texto_pregunta=pregunta_texto,
                        respuesta_correcta=".",
                        puntos=puntos
                    )
        
        modulos.append(modulo)
        print(f"  OK {titulo} - {modulo.lecciones.count()} lecciones, {len(preguntas_data)} preguntas")
    
    print(f"OK {len(modulos)} modulos creados\n")
    return modulos

def crear_retos():
    """Crear retos CTF con flag = ."""
    print(" Creando retos CTF (flag = '.')...")
    
    instructor = User.objects.get(username='inst')
    categorias = list(Categoria.objects.all())
    
    retos_data = [
        ('SQL Injection Basico', 'Inyecta SQL para bypassear el login', 'PRINCIPIANTE', 100),
        ('XSS Reflejado', 'Ejecuta JavaScript en el navegador', 'PRINCIPIANTE', 100),
        ('Command Injection', 'Ejecuta comandos en el servidor', 'INTERMEDIO', 200),
        ('Cifrado Cesar', 'Descifra el mensaje en el codigo fuente', 'PRINCIPIANTE', 100),
        ('RSA Basico', 'Factoriza el modulo RSA', 'INTERMEDIO', 200),
        ('Buffer Overflow 101', 'Desborda el buffer para ganar control', 'INTERMEDIO', 250),
        ('Crackme facil', 'Ingenieria inversa basica', 'INTERMEDIO', 200),
        ('Metadata Oculta', 'Encuentra la bandera en los metadatos', 'PRINCIPIANTE', 100),
        ('PCAP Analysis', 'Analiza el trafico capturado', 'INTERMEDIO', 200),
    ]
    
    retos = []
    for i, (titulo, desc, dificultad, puntos) in enumerate(retos_data):
        categoria = categorias[i % len(categorias)]
        reto = Reto.objects.create(
            titulo=titulo,
            descripcion=f"{desc}\n\nLa flag es un punto '.'",
            categoria=categoria,
            dificultad=dificultad,
            puntos=puntos,
            bandera=".",
            pista="Revisa los parametros",
            creado_por=instructor,
            esta_oculto=False
        )
        retos.append(reto)
        print(f"  OK {titulo} - {puntos} pts ({dificultad}) - flag: '.'")
    
    print(f"OK {len(retos)} retos creados\n")
    return retos

def crear_equipos():
    """Crear equipos con miembros"""
    print(" Creando equipos...")
    
    estudiantes = list(User.objects.filter(perfil__rol='ESTUDIANTE'))
    leo = User.objects.get(username='leo')
    
    equipos_data = [
        ('CyberQuest Elite', 'Equipo de elite de CyberQuest'),
        ('Hackers Pro', 'Los mejores hackers de la EMI'),
        ('NullByte Security', 'Especialistas en seguridad ofensiva'),
    ]
    
    equipos = []
    for i, (nombre, desc) in enumerate(equipos_data):
        lider = estudiantes[i % len(estudiantes)] if estudiantes else leo
        equipo = Equipo.objects.create(
            nombre=nombre,
            descripcion=desc,
            lider=lider,
            puntos=random.randint(500, 2000)
        )
        
        # Agregar miembros aleatorios
        otros = [e for e in estudiantes if e != lider]
        for otro in random.sample(otros, min(2, len(otros))):
            equipo.miembros.add(otro)
        
        equipos.append(equipo)
        print(f"  OK {nombre} - Lider: {lider.username} - {equipo.miembros.count()} miembros - {equipo.puntos} pts")
    
    # Equipo de Leo
    equipo_leo, _ = Equipo.objects.get_or_create(
        nombre='Team Leo',
        defaults={
            'descripcion': 'El equipo de Leo',
            'lider': leo,
            'puntos': 0
        }
    )
    equipos.append(equipo_leo)
    print(f"  OK Team Leo - Lider: leo")
    
    print(f"OK {len(equipos)} equipos creados\n")
    return equipos

def crear_intentos(usuarios, retos):
    """Crear intentos de retos"""
    print(" Creando intentos de retos...")
    
    estudiantes = [u for u in usuarios if u.perfil.rol == 'ESTUDIANTE']
    leo = User.objects.get(username='leo')
    
    # Leo resuelve retos
    for reto in random.sample(retos, min(5, len(retos))):
        IntentoReto.objects.create(
            usuario=leo,
            reto=reto,
            bandera_enviada=".",
            es_correcto=True
        )
        leo.perfil.puntos += reto.puntos
        leo.perfil.save()
    print(f"  OK Leo resolvio retos - {leo.perfil.puntos} pts")
    
    # Otros estudiantes
    for estudiante in estudiantes:
        if estudiante != leo:
            retos_resueltos = random.sample(retos, random.randint(1, 3))
            for reto in retos_resueltos:
                IntentoReto.objects.create(
                    usuario=estudiante,
                    reto=reto,
                    bandera_enviada=".",
                    es_correcto=True
                )
                estudiante.perfil.puntos += reto.puntos
                estudiante.perfil.save()
    
    print(f"OK Intentos registrados\n")

def main():
    print("=" * 70)
    print("CYBERQUEST - POBLANDO BASE DE DATOS")
    print("=" * 70 + "\n")
    
    # Ejecutar creacion
    usuarios = crear_usuarios_especificos()
    categorias = crear_categorias()
    modulos = crear_modulos_con_preguntas()
    retos = crear_retos()
    equipos = crear_equipos()
    crear_intentos(usuarios, retos)
    
    # Configuracion IA
    config, _ = ConfiguracionIA.objects.get_or_create(id=1)
    config.asistente_activo = True
    config.save()
    
    print("=" * 70)
    print("ESTADISTICAS FINALES")
    print("=" * 70)
    print(f"Usuarios: {User.objects.count()}")
    print(f"  Admin: adm / adm")
    print(f"  Instructor: inst / inst")
    print(f"  Estudiante: leo / leo")
    print(f"Categorias: {Categoria.objects.count()}")
    print(f"Retos: {Reto.objects.count()} (todos con flag = '.')")
    print(f"Modulos: {Modulo.objects.count()}")
    print(f"Lecciones: {Leccion.objects.count()}")
    print(f"Preguntas: {Pregunta.objects.count()} (respuesta = '.')")
    print(f"Equipos: {Equipo.objects.count()}")
    print(f"Puntos Leo: {User.objects.get(username='leo').perfil.puntos} pts")
    print("=" * 70)
    print(" Base de datos poblada exitosamente!")
    print("=" * 70)
    print("\nCREDENCIALES:")
    print("  adm / adm - Administrador")
    print("  inst / inst - Instructor")
    print("  leo / leo - Competidor")
    print("\nRETOS: Todos los retos tienen flag = '.'")
    print("PREGUNTAS: Todas las respuestas son '.'")
    print("=" * 70)

if __name__ == "__main__":
    main()