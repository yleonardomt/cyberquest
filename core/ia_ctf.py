# core/ia_ctf.py
# Asistente IA para CyberQuest - Respuestas inteligentes locales

from django.utils import timezone
from django.db.models import Count, Sum
from .models import Perfil, Reto, IntentoReto, Equipo, Evento, Modulo


def obtener_respuesta(usuario, pregunta):
    """
    Función principal que procesa la pregunta y devuelve una respuesta inteligente
    """
    pregunta_lower = pregunta.lower().strip()
    perfil = usuario.perfil
    
    # ========== SALUDOS ==========
    if any(word in pregunta_lower for word in ['hola', 'buenas', 'hey', 'que tal', 'saludos', 'ola', 'alo']):
        return saludar(usuario)
    
    # ========== PUNTOS ==========
    elif any(word in pregunta_lower for word in ['puntos', 'puntuación', 'puntaje']):
        return ver_puntos(perfil)
    
    # ========== POSICIÓN / RANKING ==========
    elif any(word in pregunta_lower for word in ['posicion', 'posición', 'ranking', 'lugar', 'puesto', 'clasificacion']):
        return ver_posicion(usuario, perfil)
    
    # ========== RETOS RESUELTOS ==========
    elif any(word in pregunta_lower for word in ['retos he resuelto', 'cuantos retos', 'retos resueltos', 'mis retos', 'retos completados', 'cuantos he resuelto']):
        return ver_retos_resueltos(usuario)
    
    # ========== QUÉ RETOS HAY ==========
    elif any(word in pregunta_lower for word in ['que retos', 'qué retos', 'retos hay', 'retos disponibles', 'que retos hay', 'mostrar retos']):
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
    elif any(word in pregunta_lower for word in ['cursos', 'mis cursos', 'que cursos', 'qué cursos', 'capacitacion']):
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
    return f"""👋 ¡Hola {usuario.username}! Soy CyberAI, tu asistente virtual.

📌 **Pregúntame cosas como:**
• ¿Cuántos puntos tengo?
• ¿En qué posición estoy?
• ¿Cuántos retos he resuelto?
• ¿Qué retos hay?
• ¿En qué equipo estoy?
• ¿Qué eventos hay activos?

💡 También puedes escribir "ayuda" para ver todos los comandos."""


def ver_puntos(perfil):
    puntos = perfil.puntos
    if puntos == 0:
        return "🏆 Aún no tienes puntos. ¡Comienza resolviendo retos!"
    elif puntos < 100:
        return f"🏆 Tienes **{puntos} puntos**. ¡Sigue así, cada reto suma!"
    elif puntos < 500:
        return f"🏆 Tienes **{puntos} puntos**. ¡Buen trabajo, vas por buen camino!"
    else:
        return f"🏆 Tienes **{puntos} puntos**. ¡Eres un experto! Sigue así."


def ver_posicion(usuario, perfil):
    total_usuarios = Perfil.objects.filter(esta_bloqueado=False, rol='ESTUDIANTE').count()
    posicion = Perfil.objects.filter(puntos__gt=perfil.puntos, esta_bloqueado=False, rol='ESTUDIANTE').count() + 1
    
    if total_usuarios == 0:
        return "🎯 Eres el único competidor por ahora. ¡Invita a más amigos!"
    
    mensaje = f"🎯 Estás en la **posición #{posicion}** de {total_usuarios} competidores."
    
    if posicion == 1:
        mensaje += "\n\n🏆 ¡Eres el número 1! ¡Impresionante! Sigue dominando."
    elif posicion <= 10:
        mensaje += "\n\n🌟 Estás en el top 10. ¡Sigue así para llegar al primer lugar!"
    elif posicion <= 50:
        mensaje += "\n\n📈 Buen trabajo. ¡Puedes llegar al top 10 si sigues practicando!"
    else:
        mensaje += "\n\n💪 No te preocupes, cada reto suma puntos. ¡Sigue practicando!"
    
    return mensaje


def ver_retos_resueltos(usuario):
    total_retos = Reto.objects.filter(esta_oculto=False).count()
    resueltos = IntentoReto.objects.filter(usuario=usuario, es_correcto=True).count()
    
    if total_retos == 0:
        return "📭 No hay retos disponibles aún. Vuelve más tarde."
    
    porcentaje = int(resueltos / total_retos * 100) if total_retos > 0 else 0
    
    if resueltos == 0:
        return f"📊 Aún no has resuelto ningún reto.\n\n🌱 ¡Comienza con los retos de nivel Principiante!"
    elif porcentaje < 25:
        return f"📊 Has resuelto **{resueltos} de {total_retos} retos** ({porcentaje}% completado).\n\n💪 ¡Sigue así, cada reto cuenta!"
    elif porcentaje < 50:
        return f"📊 Has resuelto **{resueltos} de {total_retos} retos** ({porcentaje}% completado).\n\n📈 ¡Vas muy bien! No te detengas."
    elif porcentaje < 75:
        return f"📊 Has resuelto **{resueltos} de {total_retos} retos** ({porcentaje}% completado).\n\n🔥 ¡Excelente progreso! Estás cerca de la cima."
    elif porcentaje < 100:
        return f"📊 Has resuelto **{resueltos} de {total_retos} retos** ({porcentaje}% completado).\n\n🏆 ¡Impresionante! Solo te faltan {total_retos - resueltos} retos para completar todo."
    else:
        return f"🏆 ¡INCREÍBLE! Has resuelto TODOS los {total_retos} retos. ¡Eres un maestro del CTF!"


def ver_retos_disponibles():
    retos = Reto.objects.filter(esta_oculto=False)[:5]
    total = Reto.objects.filter(esta_oculto=False).count()
    
    if not retos:
        return "📭 No hay retos disponibles aún. Vuelve más tarde."
    
    # Clasificar por dificultad
    principiantes = Reto.objects.filter(esta_oculto=False, dificultad='PRINCIPIANTE').count()
    intermedios = Reto.objects.filter(esta_oculto=False, dificultad='INTERMEDIO').count()
    avanzados = Reto.objects.filter(esta_oculto=False, dificultad='AVANZADO').count()
    
    lista = []
    for r in retos:
        emoji = "🌱" if r.dificultad == 'PRINCIPIANTE' else "⚡" if r.dificultad == 'INTERMEDIO' else "🔥"
        lista.append(f"{emoji} {r.titulo} ({r.puntos} pts)")
    
    return f"""🏁 **Retos disponibles:**

{chr(10).join(lista)}

📊 **Distribución:**
• 🌱 Principiantes: {principiantes}
• ⚡ Intermedios: {intermedios}
• 🔥 Avanzados: {avanzados}

💡 Hay {total} retos en total. ¡Empieza con los Principiante!"""


def total_retos():
    total = Reto.objects.filter(esta_oculto=False).count()
    return f"📊 Hay **{total} retos** en total en CyberQuest.\n\n💡 ¿Quieres saber cuántos has resuelto? Pregúntame 'mis retos'."


def ver_equipo(usuario):
    equipo = usuario.equipos.first() or usuario.equipos_liderados.first()
    
    if not equipo:
        return """⚠️ **No estás en ningún equipo.**

Puedes:
• 🔨 **Crear un nuevo equipo** - Ve a la sección Equipos
• 🔑 **Unirte con código** - Pídele el código al líder

💡 Los equipos suman puntos y pueden participar juntos en eventos CTF."""
    
    miembros = [equipo.lider.username] + [m.username for m in equipo.miembros.all()]
    
    return f"""👥 **Tu equipo: {equipo.nombre}**

• 👑 Líder: {equipo.lider.username}
• 👤 Miembros: {', '.join(miembros)}
• 📊 Puntos del equipo: {equipo.puntos}
• 👥 Total: {equipo.cantidad_miembros()} integrantes

💡 Comparte el código de invitación: `{equipo.codigo_invitacion}`"""


def ver_eventos():
    ahora = timezone.now()
    
    # Eventos activos
    activos = Evento.objects.filter(fecha_inicio__lte=ahora, fecha_fin__gte=ahora)
    if activos:
        lista = []
        for e in activos:
            tiempo = e.fecha_fin - ahora
            horas = int(tiempo.total_seconds() / 3600)
            lista.append(f"• {e.nombre} - Termina en {horas} horas")
        return f"""🎯 **Eventos CTF activos:**

{chr(10).join(lista)}

🔥 ¡Inscríbete y participa para ganar puntos extra!"""
    
    # Próximos eventos
    proximos = Evento.objects.filter(fecha_inicio__gt=ahora).order_by('fecha_inicio')[:3]
    if proximos:
        lista = []
        for e in proximos:
            tiempo = e.fecha_inicio - ahora
            horas = int(tiempo.total_seconds() / 3600)
            dias = int(horas / 24)
            if dias > 0:
                lista.append(f"• {e.nombre} - Comienza en {dias} días")
            else:
                lista.append(f"• {e.nombre} - Comienza en {horas} horas")
        return f"""⏰ **Próximos eventos CTF:**

{chr(10).join(lista)}

📅 ¡Prepárate para competir!"""
    
    return "🎯 No hay eventos activos ni próximos en este momento. ¡Pronto habrá más competencias!"


def ver_cursos():
    modulos = Modulo.objects.filter(esta_publicado=True)
    
    if not modulos:
        return "📚 Pronto habrá cursos disponibles. ¡Mantente atento a las novedades!"
    
    lista = []
    for m in modulos[:5]:
        lecciones_count = m.lecciones.count()
        lista.append(f"• {m.titulo} ({lecciones_count} lecciones)")
    
    resultado = f"📚 **Cursos disponibles:**\n\n{chr(10).join(lista)}"
    
    if modulos.count() > 5:
        resultado += f"\n\n... y {modulos.count() - 5} cursos más."
    
    resultado += "\n\n💡 Ve a 'Mis Cursos' para comenzar a aprender."
    return resultado


def mostrar_ayuda():
    return """🤖 **COMANDOS QUE ENTIENDO:**

📊 **PROGRESO PERSONAL:**
• "mis puntos" - Ver tus puntos
• "mi posición" - Ver tu lugar en el ranking
• "mis retos" - Ver cuántos retos has resuelto

🏆 **RETOS:**
• "qué retos hay" - Ver retos disponibles
• "total retos" - Ver cuántos retos hay en total

👥 **EQUIPOS:**
• "mi equipo" - Información de tu equipo

🎯 **EVENTOS:**
• "eventos activos" - Ver eventos CTF actuales

📚 **CURSOS:**
• "qué cursos hay" - Ver cursos disponibles

💬 **EJEMPLOS:**
• "¿Cuántos puntos tengo?"
• "¿En qué posición estoy?"
• "¿Cuántos retos he resuelto?"
• "Muéstrame los retos disponibles"

💡 ¡Pregúntame de forma natural! No necesitas palabras exactas."""


def respuesta_no_entendida(pregunta):
    return f"""🤔 No entendí: "{pregunta}"

**Preguntas que SÍ entiendo:**
• "hola" - Saludar
• "mis puntos" - Ver tus puntos
• "mi posición" - Ver tu ranking
• "mis retos" - Ver retos resueltos
• "qué retos hay" - Ver retos disponibles
• "total retos" - Total de retos
• "mi equipo" - Info de tu equipo
• "eventos activos" - Eventos CTF
• "qué cursos hay" - Cursos disponibles
• "ayuda" - Ver todos los comandos

💡 **Ejemplo:** "¿Cuántos puntos tengo?" o "¿En qué posición estoy?"

¿Podrías reformular tu pregunta?"""