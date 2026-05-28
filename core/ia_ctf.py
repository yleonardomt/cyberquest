# core/ia_ctf.py
# Asistente IA para CyberQuest - Respuestas inteligentes locales

from django.utils import timezone
from django.db.models import Count, Sum
from .models import Perfil, Reto, IntentoReto, Equipo, Evento, Modulo, ConfiguracionIA, ConsultaIA


def obtener_respuesta(usuario, pregunta):
    """
    Funcion principal que procesa la pregunta y devuelve una respuesta inteligente
    """
    # Obtener configuracion
    config = ConfiguracionIA.objects.first()
    
    # Verificar si el asistente esta habilitado
    if not config or not config.asistente_activo:
        return "El asistente IA ha sido deshabilitado por el administrador. Por favor, intenta mas tarde."
    
    pregunta_lower = pregunta.lower().strip()
    perfil = usuario.perfil
    
    # ========== SALUDOS ==========
    if any(word in pregunta_lower for word in ['hola', 'buenas', 'hey', 'que tal', 'saludos', 'ola', 'alo']):
        return saludar(usuario)
    
    # ========== PUNTOS ==========
    elif any(word in pregunta_lower for word in ['puntos', 'puntuacion', 'puntaje', 'mis puntos', 'cuantos puntos']):
        return ver_puntos(perfil)
    
    # ========== POSICION / RANKING ==========
    elif any(word in pregunta_lower for word in ['posicion', 'ranking', 'lugar', 'puesto', 'clasificacion', 'en que lugar']):
        return ver_posicion(usuario, perfil)
    
    # ========== RETOS RESUELTOS ==========
    elif any(word in pregunta_lower for word in ['retos he resuelto', 'cuantos retos', 'retos resueltos', 'mis retos', 'retos completados', 'cuantos he resuelto']):
        return ver_retos_resueltos(usuario)
    
    # ========== QUE RETOS HAY ==========
    elif any(word in pregunta_lower for word in ['que retos', 'retos hay', 'retos disponibles', 'mostrar retos']):
        return ver_retos_disponibles()
    
    # ========== TOTAL DE RETOS ==========
    elif any(word in pregunta_lower for word in ['total retos', 'cuantos retos hay en total', 'cuantos retos existen', 'retos en total']):
        return total_retos()
    
    # ========== EQUIPO ==========
    elif any(word in pregunta_lower for word in ['equipo', 'team', 'mi equipo', 'en que equipo']):
        return ver_equipo(usuario)
    
    # ========== EVENTOS ACTIVOS ==========
    elif any(word in pregunta_lower for word in ['eventos activos', 'eventos hay', 'evento activo', 'ctf activo', 'que eventos hay', 'eventos ctf']):
        return ver_eventos()
    
    # ========== CURSOS ==========
    elif any(word in pregunta_lower for word in ['cursos', 'mis cursos', 'que cursos', 'capacitacion']):
        return ver_cursos()
    
    # ========== AYUDA ==========
    elif any(word in pregunta_lower for word in ['ayuda', 'comandos', 'que puedes hacer', 'como usas', 'help']):
        return mostrar_ayuda()
    
    # ========== RESPUESTA POR DEFECTO ==========
    else:
        return respuesta_no_entendida(pregunta)


# ============================================================
# FUNCIONES DE RESPUESTA
# ============================================================

def saludar(usuario):
    return f"""Hola {usuario.username}! Soy CyberAI, tu asistente virtual.

Preguntame cosas como:
- Cuantos puntos tengo?
- En que posicion estoy?
- Cuantos retos he resuelto?
- Que retos hay?
- En que equipo estoy?
- Que eventos hay activos?

Escribe "ayuda" para ver todos los comandos."""


def ver_puntos(perfil):
    puntos = perfil.puntos
    if puntos == 0:
        return "Aun no tienes puntos. Comienza resolviendo retos!"
    elif puntos < 100:
        return f"Tienes {puntos} puntos. Sigue asi, cada reto suma!"
    elif puntos < 500:
        return f"Tienes {puntos} puntos. Buen trabajo, vas por buen camino!"
    else:
        return f"Tienes {puntos} puntos. Eres un experto! Sigue asi."


def ver_posicion(usuario, perfil):
    total_usuarios = Perfil.objects.filter(esta_bloqueado=False, rol='ESTUDIANTE').count()
    posicion = Perfil.objects.filter(puntos__gt=perfil.puntos, esta_bloqueado=False, rol='ESTUDIANTE').count() + 1
    
    if total_usuarios == 0:
        return "Eres el unico competidor por ahora. Invita a mas amigos!"
    
    mensaje = f"Estas en la posicion #{posicion} de {total_usuarios} competidores."
    
    if posicion == 1:
        mensaje += "\n\nEres el numero 1! Impresionante! Sigue dominando."
    elif posicion <= 10:
        mensaje += "\n\nEstas en el top 10. Sigue asi para llegar al primer lugar!"
    elif posicion <= 50:
        mensaje += "\n\nBuen trabajo. Puedes llegar al top 10 si sigues practicando!"
    else:
        mensaje += "\n\nNo te preocupes, cada reto suma puntos. Sigue practicando!"
    
    return mensaje


def ver_retos_resueltos(usuario):
    total_retos = Reto.objects.filter(esta_oculto=False).count()
    resueltos = IntentoReto.objects.filter(usuario=usuario, es_correcto=True).count()
    
    if total_retos == 0:
        return "No hay retos disponibles aun. Vuelve mas tarde."
    
    porcentaje = int(resueltos / total_retos * 100) if total_retos > 0 else 0
    
    if resueltos == 0:
        return f"Aun no has resuelto ningun reto.\n\nComienza con los retos de nivel Principiante!"
    elif porcentaje < 25:
        return f"Has resuelto {resueltos} de {total_retos} retos ({porcentaje}% completado).\n\nSigue asi, cada reto cuenta!"
    elif porcentaje < 50:
        return f"Has resuelto {resueltos} de {total_retos} retos ({porcentaje}% completado).\n\nVas muy bien! No te detengas."
    elif porcentaje < 75:
        return f"Has resuelto {resueltos} de {total_retos} retos ({porcentaje}% completado).\n\nExcelente progreso! Estas cerca de la cima."
    elif porcentaje < 100:
        return f"Has resuelto {resueltos} de {total_retos} retos ({porcentaje}% completado).\n\nImpresionante! Solo te faltan {total_retos - resueltos} retos para completar todo."
    else:
        return f"INCREIBLE! Has resuelto TODOS los {total_retos} retos. Eres un maestro del CTF!"


def ver_retos_disponibles():
    retos = Reto.objects.filter(esta_oculto=False)[:5]
    total = Reto.objects.filter(esta_oculto=False).count()
    
    if not retos:
        return "No hay retos disponibles aun. Vuelve mas tarde."
    
    # Clasificar por dificultad
    principiantes = Reto.objects.filter(esta_oculto=False, dificultad='PRINCIPIANTE').count()
    intermedios = Reto.objects.filter(esta_oculto=False, dificultad='INTERMEDIO').count()
    avanzados = Reto.objects.filter(esta_oculto=False, dificultad='AVANZADO').count()
    
    lista = []
    for r in retos:
        dificultad = ""
        if r.dificultad == 'PRINCIPIANTE':
            dificultad = "[Principiante]"
        elif r.dificultad == 'INTERMEDIO':
            dificultad = "[Intermedio]"
        else:
            dificultad = "[Avanzado]"
        lista.append(f"{dificultad} {r.titulo} ({r.puntos} pts)")
    
    return f"""Retos disponibles:

{chr(10).join(lista)}

Distribucion:
- Principiantes: {principiantes}
- Intermedios: {intermedios}
- Avanzados: {avanzados}

Hay {total} retos en total. Empieza con los Principiante!"""


def total_retos():
    total = Reto.objects.filter(esta_oculto=False).count()
    return f"Hay {total} retos en total en CyberQuest.\n\nQuieres saber cuantos has resuelto? Preguntame 'mis retos'."


def ver_equipo(usuario):
    equipo = usuario.equipos.first() or usuario.equipos_liderados.first()
    
    if not equipo:
        return """No estas en ningun equipo.

Puedes:
- Crear un nuevo equipo - Ve a la seccion Equipos
- Unirte con codigo - Pidele el codigo al lider

Los equipos suman puntos y pueden participar juntos en eventos CTF."""
    
    miembros = [equipo.lider.username] + [m.username for m in equipo.miembros.all()]
    
    return f"""Tu equipo: {equipo.nombre}

- Lider: {equipo.lider.username}
- Miembros: {', '.join(miembros)}
- Puntos del equipo: {equipo.puntos}
- Total: {equipo.cantidad_miembros} integrantes

Comparte el codigo de invitacion: {equipo.codigo_invitacion}"""


def ver_eventos():
    ahora = timezone.now()
    
    # Eventos activos
    activos = Evento.objects.filter(fecha_inicio__lte=ahora, fecha_fin__gte=ahora)
    if activos:
        lista = []
        for e in activos:
            tiempo = e.fecha_fin - ahora
            horas = int(tiempo.total_seconds() / 3600)
            lista.append(f"- {e.nombre} - Termina en {horas} horas")
        return f"""Eventos CTF activos:

{chr(10).join(lista)}

Inscribete y participa para ganar puntos extra!"""
    
    # Proximos eventos
    proximos = Evento.objects.filter(fecha_inicio__gt=ahora).order_by('fecha_inicio')[:3]
    if proximos:
        lista = []
        for e in proximos:
            tiempo = e.fecha_inicio - ahora
            horas = int(tiempo.total_seconds() / 3600)
            dias = int(horas / 24)
            if dias > 0:
                lista.append(f"- {e.nombre} - Comienza en {dias} dias")
            else:
                lista.append(f"- {e.nombre} - Comienza en {horas} horas")
        return f"""Proximos eventos CTF:

{chr(10).join(lista)}

Preparate para competir!"""
    
    return "No hay eventos activos ni proximos en este momento. Pronto habra mas competencias!"


def ver_cursos():
    modulos = Modulo.objects.filter(esta_publicado=True)
    
    if not modulos:
        return "Pronto habra cursos disponibles. Mantente atento a las novedades!"
    
    lista = []
    for m in modulos[:5]:
        lecciones_count = m.lecciones.count()
        lista.append(f"- {m.titulo} ({lecciones_count} lecciones)")
    
    resultado = f"Cursos disponibles:\n\n{chr(10).join(lista)}"
    
    if modulos.count() > 5:
        resultado += f"\n\n... y {modulos.count() - 5} cursos mas."
    
    resultado += "\n\nVe a 'Mis Cursos' para comenzar a aprender."
    return resultado


def mostrar_ayuda():
    return """COMANDOS QUE ENTIENDO:

PROGRESO PERSONAL:
- "mis puntos" - Ver tus puntos
- "mi posicion" - Ver tu lugar en el ranking
- "mis retos" - Ver cuantos retos has resuelto

RETOS:
- "que retos hay" - Ver retos disponibles
- "total retos" - Ver cuantos retos hay en total

EQUIPOS:
- "mi equipo" - Informacion de tu equipo

EVENTOS:
- "eventos activos" - Ver eventos CTF actuales

CURSOS:
- "que cursos hay" - Ver cursos disponibles

EJEMPLOS:
- "Cuantos puntos tengo?"
- "En que posicion estoy?"
- "Cuantos retos he resuelto?"
- "Muestrame los retos disponibles"

Preguntame de forma natural! No necesitas palabras exactas."""


def respuesta_no_entendida(pregunta):
    return f"""No entendi: "{pregunta}"

Preguntas que SI entiendo:
- "hola" - Saludar
- "mis puntos" - Ver tus puntos
- "mi posicion" - Ver tu ranking
- "mis retos" - Ver retos resueltos
- "que retos hay" - Ver retos disponibles
- "total retos" - Total de retos
- "mi equipo" - Info de tu equipo
- "eventos activos" - Eventos CTF
- "que cursos hay" - Cursos disponibles
- "ayuda" - Ver todos los comandos

Ejemplo: "Cuantos puntos tengo?" o "En que posicion estoy?"

Puedes reformular tu pregunta?"""