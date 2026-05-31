from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime
import uuid
import os
import docker
import traceback
from django.conf import settings
from django.db.models import Count, Sum, Q
import json
from core.utils.ratelimit import ratelimit
from .models import (
    Perfil,
    RestablecerContrasena,
    Categoria,
    Reto,
    RecursoReto,
    IntentoReto,
    # CalificacionReto,  # COMENTADO - No existe en models.py
    Entorno,
    # InformeTecnico,   # COMENTADO - No existe en models.py
    ConsultaIA,
    Equipo,
    InvitacionEquipo,
    Modulo,
    Leccion,
    Recurso,
    Pregunta,
    ProgresoUsuario,
    Certificado,
    EnvioBandera,
    RegistroAuditoria,
    Evento,
    # Ticket,           # COMENTADO - No existe en models.py
    ConfiguracionIA,
    # DocumentoIA,      # COMENTADO - No existe en models.py
)
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.sessions.models import Session
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from django.http import HttpResponse
from django.apps import apps  # Para obtener modelos dinámicamente si es necesario
# ============================================================
# VISTAS PÚBLICAS
# ============================================================


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Validar nombre de usuario único
        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe")
            return render(request, "register.html")
        
        # Validar correo único
        if User.objects.filter(email=email).exists():
            messages.error(request, "El correo ya está registrado")
            return render(request, "register.html")
        
        # VALIDAR CONTRASEÑA CON LOS VALIDADORES
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, "register.html")

        # Si todo está bien, crear el usuario
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        Perfil.objects.create(usuario=user)
        messages.success(request, "¡Registro exitoso! Ahora inicia sesión")
        return redirect("login")

    return render(request, "register.html")

@ratelimit(key='ip', rate=5, timeout=300)
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if hasattr(user, "perfil") and user.perfil.esta_bloqueado:
                messages.error(
                    request, "Tu cuenta está bloqueada. Contacta al administrador."
                )
                return render(request, "login.html")

            login(request, user)

            RegistroAuditoria.objects.create(
                usuario=user,
                accion="INICIAR_SESION",
                direccion_ip=request.META.get("REMOTE_ADDR"),
            )

            return redirect("dashboard")
        else:
            messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "login.html")


def logout_view(request):
    if request.user.is_authenticated:
        # Registrar el cierre de sesión en auditoría
        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion="CERRAR_SESION",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )
        
        # Eliminar la sesión de la base de datos manualmente
        from django.contrib.sessions.models import Session
        if request.session.session_key:
            try:
                Session.objects.filter(session_key=request.session.session_key).delete()
            except:
                pass
    
    # Cerrar sesión de Django
    logout(request)
    
    return redirect("home")



def reset_password_request(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)

            token = str(uuid.uuid4())
            expires = timezone.now() + timedelta(hours=24)

            RestablecerContrasena.objects.create(
                usuario=user, token=token, expira_en=expires
            )

            reset_link = request.build_absolute_uri(f"/reset/{token}/")

            send_mail(
                "Recuperación de contraseña - CyberQuest",
                f"""
Hola {user.username}

Haz clic en el siguiente enlace para recuperar tu contraseña:

{reset_link}

Este enlace expira en 24 horas.
                """,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            messages.success(request, "Correo de recuperación enviado correctamente")

        except User.DoesNotExist:
            messages.error(request, "No existe una cuenta con este correo")

        except Exception as e:
            messages.error(request, f"Error enviando correo: {e}")

    return render(request, "reset_password.html")


def reset_password_confirm(request, token):
    try:
        pr = RestablecerContrasena.objects.get(
            token=token, usado=False, expira_en__gt=timezone.now()
        )
        if request.method == "POST":
            password = request.POST.get("password")
            password2 = request.POST.get("password2")
            if password == password2:
                pr.usuario.set_password(password)
                pr.usuario.save()
                pr.usado = True
                pr.save()
                messages.success(request, "Contraseña actualizada correctamente")
                return redirect("login")
            else:
                messages.error(request, "Las contraseñas no coinciden")
        return render(request, "reset_confirm.html", {"token": token})
    except RestablecerContrasena.DoesNotExist:
        messages.error(request, "Token inválido o expirado")
        return redirect("login")


# ============================================================
# DASHBOARD Y PERFIL
# ============================================================


@login_required
def dashboard(request):
    perfil = request.user.perfil
    rol = perfil.rol

    retos_completados = IntentoReto.objects.filter(
        usuario=request.user, es_correcto=True
    ).count()

    puntos_totales = perfil.puntos

    equipo = request.user.equipos.first() or request.user.equipos_liderados.first()
    equipo_nombre = equipo.nombre if equipo else "Sin equipo"

    posicion = (
        Perfil.objects.filter(puntos__gt=perfil.puntos, esta_bloqueado=False).count()
        + 1
    )

    total_retos = Reto.objects.filter(esta_oculto=False).count()
    porcentaje_progreso = (
        int((retos_completados / total_retos * 100)) if total_retos > 0 else 0
    )

    actividad_reciente = RegistroAuditoria.objects.filter(
        usuario=request.user
    ).order_by("-timestamp")[:5]

    context = {
        "perfil": perfil,
        "rol": rol,
        "retos_completados": retos_completados,
        "puntos_totales": puntos_totales,
        "equipo_nombre": equipo_nombre,
        "posicion": f"#{posicion}",
        "porcentaje_progreso": porcentaje_progreso,
        "actividad_reciente": actividad_reciente,
    }

    if rol == "ADMIN":
        context.update(
            {
                "total_usuarios": Perfil.objects.count(),
                "total_retos": Reto.objects.filter(esta_oculto=False).count(),
                "total_eventos": Evento.objects.count(),
                "total_equipos": Equipo.objects.count(),
                "total_puntos": Perfil.objects.aggregate(total=Sum("puntos"))["total"]
                or 0,
                "retos_resueltos_total": IntentoReto.objects.filter(
                    es_correcto=True
                ).count(),
            }
        )

    if rol == "INSTRUCTOR":
        context.update(
            {
                "mis_cursos": Modulo.objects.filter(creado_por=request.user).count(),
                "mis_retos": Reto.objects.filter(creado_por=request.user).count(),
                "mis_eventos": Evento.objects.filter(creado_por=request.user).count(),
            }
        )

    return render(request, "dashboard.html", context)


@login_required
def perfil_detalle(request):
    perfil = request.user.perfil

    retos_completados = IntentoReto.objects.filter(
        usuario=request.user, es_correcto=True
    ).count()

    posicion = (
        Perfil.objects.filter(puntos__gt=perfil.puntos, esta_bloqueado=False).count()
        + 1
    )

    context = {
        "perfil": perfil,
        "retos_completados": retos_completados,
        "posicion": posicion,
        "rol": perfil.rol,
    }
    return render(request, "profile_detail.html", context)


@login_required
def perfil_editar(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        telefono = request.POST.get("telefono")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        
        usuario = request.user
        perfil = usuario.perfil
        
        # Variables para controlar si la sesión debe mantenerse
        password_changed = False

        # Validar username único
        if username and username != usuario.username:
            if User.objects.filter(username=username).exists():
                messages.error(request, "El nombre de usuario ya existe")
                return redirect("perfil_editar")
            usuario.username = username

        # Actualizar email
        if email:
            usuario.email = email

        # Actualizar teléfono
        if telefono:
            perfil.telefono = telefono

        # Cambiar contraseña si se proporcionó
        if password and password == password2:
            usuario.set_password(password)
            password_changed = True
            messages.success(request, "Contraseña actualizada correctamente. Por favor, inicia sesión nuevamente con tu nueva contraseña.")
        elif password and password != password2:
            messages.error(request, "Las contraseñas no coinciden")
            return redirect("perfil_editar")

        # Guardar cambios del usuario
        usuario.save()
        
        # Guardar cambios del perfil
        perfil.save()

        # Actualizar avatar
        if request.FILES.get("avatar"):
            if perfil.avatar:
                perfil.avatar.delete()
            perfil.avatar = request.FILES["avatar"]
            perfil.save()

        # Si se cambió la contraseña, cerrar sesión y pedir que inicie nuevamente
        if password_changed:
            from django.contrib.auth import logout
            logout(request)
            messages.info(request, "Tu sesión ha sido cerrada. Inicia sesión con tu nueva contraseña.")
            return redirect("login")

        messages.success(request, "Perfil actualizado correctamente")
        return redirect("perfil_detalle")

    context = {
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "profile_edit.html", context)


# ============================================================
# CRUD USUARIOS (ADMIN)
# ============================================================


@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def listar_usuarios(request):
    usuarios = Perfil.objects.all().select_related("usuario").order_by("-puntos")
    return render(request, "user_list.html", {"usuarios": usuarios})


@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def crear_usuario(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        rol = request.POST.get("rol")

        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe")
            return redirect("crear_usuario")

        if User.objects.filter(email=email).exists():
            messages.error(request, "El correo ya está registrado")
            return redirect("crear_usuario")

        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        Perfil.objects.create(usuario=user, rol=rol)

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"CREAR_USUARIO: {username}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, f'Usuario "{username}" creado exitosamente')
        return redirect("listar_usuarios")

    return render(request, "user_create.html")


@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def editar_usuario(request, user_id):
    perfil = get_object_or_404(Perfil, id=user_id)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        rol = request.POST.get("rol")

        # Validar username único
        if username and username != perfil.usuario.username:
            if User.objects.filter(username=username).exclude(id=perfil.usuario.id).exists():
                messages.error(request, "El nombre de usuario ya existe")
                return redirect("editar_usuario", user_id=user_id)
            perfil.usuario.username = username

        # Cambiar contraseña solo si se proporcionó
        if password and password.strip():
            perfil.usuario.set_password(password)

        # Actualizar rol
        perfil.rol = rol
        perfil.usuario.save()
        perfil.save()

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"EDITAR_USUARIO: {perfil.usuario.username}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, f'Usuario "{perfil.usuario.username}" actualizado correctamente')
        return redirect("listar_usuarios")

    return render(request, "user_edit.html", {"perfil": perfil})


@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def eliminar_usuario(request, user_id):
    perfil = get_object_or_404(Perfil, id=user_id)
    username = perfil.usuario.username

    if perfil.usuario == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta")
        return redirect("listar_usuarios")

    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"ELIMINAR_USUARIO: {username}",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    perfil.usuario.delete()
    messages.success(request, f'Usuario "{username}" eliminado correctamente')
    return redirect("listar_usuarios")


@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def bloquear_usuario(request, user_id):
    perfil = get_object_or_404(Perfil, id=user_id)
    perfil.esta_bloqueado = not perfil.esta_bloqueado
    perfil.save()

    estado = "bloqueado" if perfil.esta_bloqueado else "desbloqueado"
    messages.success(request, f"Usuario {perfil.usuario.username} {estado}")

    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"BLOQUEAR_USUARIO_{estado.upper()}: {perfil.usuario.username}",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    return redirect("listar_usuarios")


# ============================================================
# EQUIPOS
# ============================================================


@login_required
def crear_equipo(request):
    # Verificar si ya pertenece a un equipo
    if request.user.equipos.exists() or request.user.equipos_liderados.exists():
        messages.error(request, "Ya perteneces a un equipo. No puedes crear otro.")
        return redirect("listar_equipos")

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion", "")

        if Equipo.objects.filter(nombre=nombre).exists():
            messages.error(request, "Ya existe un equipo con ese nombre")
        else:
            equipo = Equipo.objects.create(
                nombre=nombre, descripcion=descripcion, lider=request.user
            )

            RegistroAuditoria.objects.create(
                usuario=request.user,
                accion=f"CREAR_EQUIPO: {nombre}",
                direccion_ip=request.META.get("REMOTE_ADDR"),
            )

            messages.success(request, f'Equipo "{nombre}" creado exitosamente')
            return redirect("listar_equipos")

    context = {
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "team_create.html", context)


@login_required
def unirse_equipo(request):
    # Verificar si ya pertenece a un equipo
    if request.user.equipos.exists() or request.user.equipos_liderados.exists():
        messages.error(request, "Ya perteneces a un equipo. No puedes unirte a otro.")
        return redirect("listar_equipos")

    if request.method == "POST":
        codigo = request.POST.get("codigo")

        try:
            equipo = Equipo.objects.get(codigo_invitacion=codigo)

            # Verificar si ya es miembro o lider
            if request.user == equipo.lider:
                messages.warning(request, f'Ya eres el lider del equipo "{equipo.nombre}"')
                return redirect("ver_equipo", equipo_id=equipo.id)

            if request.user in equipo.miembros.all():
                messages.warning(request, f'Ya eres miembro del equipo "{equipo.nombre}"')
                return redirect("ver_equipo", equipo_id=equipo.id)

            # Unirse al equipo
            equipo.miembros.add(request.user)

            RegistroAuditoria.objects.create(
                usuario=request.user,
                accion=f"UNIRSE_EQUIPO: {equipo.nombre}",
                direccion_ip=request.META.get("REMOTE_ADDR"),
            )

            messages.success(request, f'Te has unido al equipo "{equipo.nombre}" exitosamente')
            return redirect("ver_equipo", equipo_id=equipo.id)

        except Equipo.DoesNotExist:
            messages.error(request, "Codigo de invitacion invalido. Verifica el codigo e intenta nuevamente.")
            return redirect("unirse_equipo")

    return render(request, "team_join.html")


@login_required
def ver_equipo(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)

    # Forzar recarga de la instancia para obtener los puntos actualizados
    equipo = Equipo.objects.get(id=equipo_id)

    # Verificar si el usuario es miembro
    es_miembro = request.user == equipo.lider or request.user in equipo.miembros.all()

    # Calcular total de miembros
    total_miembros = equipo.miembros.count() + 1

    context = {
        'equipo': equipo,
        'es_miembro': es_miembro,
        'total_miembros': total_miembros,
        'perfil': request.user.perfil,
        'rol': request.user.perfil.rol,
    }
    return render(request, 'team_detail.html', context)


@login_required
def listar_equipos(request):
    # Mostrar TODOS los equipos sin restricciones
    todos_equipos = Equipo.objects.all().order_by('-puntos')

    # Verificar si el usuario pertenece a algun equipo
    mi_equipo = None
    if request.user.equipos.exists():
        mi_equipo = request.user.equipos.first()
    elif request.user.equipos_liderados.exists():
        mi_equipo = request.user.equipos_liderados.first()

    # Retos resueltos por el equipo del usuario (si tiene)
    retos_equipo = []
    if mi_equipo:
        miembros_ids = [mi_equipo.lider.id] + list(mi_equipo.miembros.values_list('id', flat=True))
        retos_equipo = Reto.objects.filter(
            intentoreto__usuario_id__in=miembros_ids,
            intentoreto__es_correcto=True
        ).distinct()

    context = {
        'todos_equipos': todos_equipos,  # Todos los equipos visibles
        'mi_equipo': mi_equipo,
        'retos_equipo': retos_equipo,
        'perfil': request.user.perfil,
        'rol': request.user.perfil.rol,
    }
    return render(request, 'team_list.html', context)


@login_required
def salir_equipo(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)

    # El líder no puede salir, debe eliminar el equipo o transferir liderazgo
    if request.user == equipo.lider:
        messages.error(
            request,
            "Eres el líder del equipo. No puedes salir. Elimina el equipo o transfiere el liderazgo.",
        )
    elif request.user in equipo.miembros.all():
        equipo.miembros.remove(request.user)

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"SALIR_EQUIPO: {equipo.nombre}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, f'Has salido del equipo "{equipo.nombre}"')
    else:
        messages.error(request, "No eres miembro de este equipo")

    return redirect("listar_equipos")


@login_required
def enviar_bandera_equipo(request, equipo_id):
    if request.method == "POST":
        try:
            equipo = get_object_or_404(Equipo, id=equipo_id)

            if request.user != equipo.lider and request.user not in equipo.miembros.all():
                return JsonResponse(
                    {"success": False, "message": "No eres miembro de este equipo"}
                )

            reto_id = request.POST.get("reto_id")
            bandera = request.POST.get("bandera", "").strip()

            if not reto_id:
                return JsonResponse(
                    {"success": False, "message": "ID del reto no proporcionado"}
                )

            reto = get_object_or_404(Reto, id=reto_id)

            intento_existente = IntentoReto.objects.filter(
                usuario=request.user, reto=reto
            ).first()

            if intento_existente and intento_existente.es_correcto:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Ya resolviste este reto anteriormente",
                    }
                )

            if bandera == reto.bandera:
                if intento_existente:
                    intento_existente.es_correcto = True
                    intento_existente.bandera_enviada = bandera
                    intento_existente.save()
                else:
                    IntentoReto.objects.create(
                        usuario=request.user,
                        reto=reto,
                        bandera_enviada=bandera,
                        es_correcto=True,
                    )

                # Sumar puntos al usuario
                request.user.perfil.puntos += reto.puntos
                request.user.perfil.save()

                # Sumar puntos al equipo
                equipo.puntos += reto.puntos
                equipo.save()

                # Actualizar la instancia para respuesta
                equipo = Equipo.objects.get(id=equipo_id)

                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Correcto! Has ganado {reto.puntos} puntos para tu equipo",
                    }
                )
            else:
                if not intento_existente:
                    IntentoReto.objects.create(
                        usuario=request.user,
                        reto=reto,
                        bandera_enviada=bandera,
                        es_correcto=False,
                    )
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Bandera incorrecta. Intenta de nuevo",
                    }
                )

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error: {str(e)}"})

    return JsonResponse({"success": False, "message": "Método no permitido"})



@login_required
def equipo_retos(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)

    if request.user != equipo.lider and request.user not in equipo.miembros.all():
        messages.error(request, "No tienes permiso para ver los retos de este equipo")
        return redirect("listar_equipos")

    retos = Reto.objects.filter(esta_oculto=False)

    miembros_ids = [equipo.lider.id] + list(equipo.miembros.values_list("id", flat=True))
    retos_resueltos = (
        IntentoReto.objects.filter(usuario_id__in=miembros_ids, es_correcto=True)
        .values_list("reto_id", flat=True)
        .distinct()
    )
    retos_resueltos_ids = list(retos_resueltos)

    for reto in retos:
        reto.entorno_activo = Entorno.objects.filter(
            usuario=request.user, reto=reto, estado="EJECUTANDO"
        ).first()

    context = {
        "equipo": equipo,
        "retos": retos,
        "retos_resueltos_ids": retos_resueltos_ids,
        "retos_resueltos_count": len(retos_resueltos_ids),
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "team_retos.html", context)

# ============================================================
# MÓDULOS Y APRENDIZAJE
# ============================================================

@login_required
def listar_modulos(request):
    modulos = Modulo.objects.all()

    if request.user.perfil.rol == "ESTUDIANTE":
        modulos = modulos.filter(esta_publicado=True)

    buscar = request.GET.get("buscar")
    if buscar:
        modulos = modulos.filter(titulo__icontains=buscar)

    if request.user.perfil.rol == "ESTUDIANTE":
        # Lista para almacenar módulos con datos de progreso
        modulos_con_progreso = []
        
        for modulo in modulos:
            lecciones = modulo.lecciones.all()
            total_lecciones = lecciones.count()
            lecciones_completadas = 0
            puntos_totales = 0
            puntos_obtenidos = 0

            for leccion in lecciones:
                progreso = ProgresoUsuario.objects.filter(
                    usuario=request.user, leccion=leccion
                ).first()

                if progreso and progreso.completado:
                    lecciones_completadas += 1
                    puntos_obtenidos += progreso.puntaje

                # Calcular puntos máximos de la lección
                puntos_leccion = sum(p.puntos for p in leccion.preguntas.all())
                puntos_totales += puntos_leccion

            # Calcular porcentaje
            porcentaje = int((lecciones_completadas / total_lecciones * 100)) if total_lecciones > 0 else 0
            
            # Agregar atributos dinámicos al módulo
            modulo.lecciones_completadas = lecciones_completadas
            modulo.porcentaje_progreso = porcentaje
            modulo.puntos_obtenidos = puntos_obtenidos
            modulo.puntos_totales = puntos_totales
            
            modulos_con_progreso.append(modulo)

        # === FILTRO POR ESTADO (RF-24) ===
        estado = request.GET.get("estado")
        if estado == "completado":
            modulos_filtrados = [m for m in modulos_con_progreso if m.porcentaje_progreso == 100]
        elif estado == "progreso":
            modulos_filtrados = [m for m in modulos_con_progreso if 0 < m.porcentaje_progreso < 100]
        elif estado == "pendiente":
            modulos_filtrados = [m for m in modulos_con_progreso if m.porcentaje_progreso == 0]
        else:
            modulos_filtrados = modulos_con_progreso

        # Estadísticas generales (sin aplicar filtro de búsqueda para los totales)
        if not buscar:
            modulos_completados = len([m for m in modulos_con_progreso if m.porcentaje_progreso == 100])
            modulos_en_progreso = len([m for m in modulos_con_progreso if 0 < m.porcentaje_progreso < 100])
            porcentaje_total = int(sum(m.porcentaje_progreso for m in modulos_con_progreso) / len(modulos_con_progreso)) if modulos_con_progreso else 0
        else:
            modulos_completados = 0
            modulos_en_progreso = 0
            porcentaje_total = 0

        context = {
            "modulos": modulos_filtrados,
            "total_modulos": len(modulos_con_progreso),
            "modulos_completados": modulos_completados,
            "modulos_en_progreso": modulos_en_progreso,
            "porcentaje_total": porcentaje_total,
            "perfil": request.user.perfil,
            "rol": request.user.perfil.rol,
        }
    else:
        # Para INSTRUCTOR y ADMIN - sin cálculos de progreso
        context = {
            "modulos": modulos,
            "perfil": request.user.perfil,
            "rol": request.user.perfil.rol,
        }

    return render(request, "module_list.html", context)


@login_required
@user_passes_test(lambda u: u.perfil.rol == "INSTRUCTOR")
def crear_modulo(request):
    if request.method == "POST":
        modulo = Modulo.objects.create(
            titulo=request.POST.get("titulo"),
            descripcion=request.POST.get("descripcion"),
            creado_por=request.user,
        )

        for key, value in request.POST.items():
            if key.startswith("leccion_titulo_"):
                idx = key.split("_")[-1]
                titulo = value
                contenido = request.POST.get(f"leccion_contenido_{idx}", "")
                orden = request.POST.get(f"leccion_orden_{idx}", 0)

                if titulo:
                    leccion = Leccion.objects.create(
                        modulo=modulo, titulo=titulo, contenido=contenido, orden=orden
                    )

                    for rkey, rvalue in request.POST.items():
                        if rkey.startswith(f"recurso_titulo_{idx}_"):
                            ridx = rkey.split("_")[-1]
                            recurso_titulo = rvalue
                            recurso_enlace = request.POST.get(
                                f"recurso_enlace_{idx}_{ridx}", ""
                            )
                            if recurso_titulo:
                                Recurso.objects.create(
                                    leccion=leccion,
                                    titulo=recurso_titulo,
                                    enlace=recurso_enlace,
                                )

                    for pkey, pvalue in request.POST.items():
                        if pkey.startswith(f"pregunta_texto_{idx}_"):
                            pidx = pkey.split("_")[-1]
                            pregunta_texto = pvalue
                            pregunta_respuesta = request.POST.get(
                                f"pregunta_respuesta_{idx}_{pidx}", ""
                            )
                            pregunta_puntos = request.POST.get(
                                f"pregunta_puntos_{idx}_{pidx}", 10
                            )
                            if pregunta_texto:
                                Pregunta.objects.create(
                                    leccion=leccion,
                                    texto_pregunta=pregunta_texto,
                                    respuesta_correcta=pregunta_respuesta,
                                    puntos=pregunta_puntos,
                                )

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"CREAR_MODULO: {modulo.titulo}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, f'Módulo "{modulo.titulo}" creado exitosamente')
        return redirect("dashboard")

    context = {
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "module_create.html", context)


@login_required
@user_passes_test(lambda u: u.perfil.rol in ["INSTRUCTOR", "ADMIN"])
def editar_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)

    if request.method == "POST":
        modulo.titulo = request.POST.get("titulo")
        modulo.descripcion = request.POST.get("descripcion")
        modulo.esta_publicado = request.POST.get("esta_publicado") == "on"
        modulo.save()

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"EDITAR_MODULO: {modulo.titulo}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, f'Módulo "{modulo.titulo}" actualizado correctamente')
        return redirect("listar_modulos")

    context = {
        "modulo": modulo,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "module_edit.html", context)


@login_required
@user_passes_test(lambda u: u.perfil.rol in ["INSTRUCTOR", "ADMIN"])
def eliminar_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)
    titulo = modulo.titulo

    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"ELIMINAR_MODULO: {titulo}",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    modulo.delete()
    messages.success(request, f'Módulo "{titulo}" eliminado correctamente')
    return redirect("listar_modulos")


@login_required
@user_passes_test(lambda u: u.perfil.rol in ["INSTRUCTOR", "ADMIN"])
def agregar_leccion(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)
    if request.method == "POST":
        leccion = Leccion.objects.create(
            modulo=modulo,
            titulo=request.POST.get("titulo"),
            contenido=request.POST.get("contenido"),
            orden=request.POST.get("orden", 0),
        )

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"CREAR_LECCION: {leccion.titulo} (Módulo: {modulo.titulo})",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, f'Lección "{leccion.titulo}" agregada correctamente')
    return redirect("editar_modulo", modulo_id=modulo_id)


@login_required
@user_passes_test(lambda u: u.perfil.rol in ["INSTRUCTOR", "ADMIN"])
def editar_leccion(request, leccion_id):
    leccion = get_object_or_404(Leccion, id=leccion_id)

    if request.method == "POST":
        leccion.titulo = request.POST.get("titulo")
        leccion.contenido = request.POST.get("contenido")
        leccion.orden = request.POST.get("orden", 0)
        leccion.save()

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"EDITAR_LECCION: {leccion.titulo}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(
            request, f'Lección "{leccion.titulo}" actualizada correctamente'
        )

    return redirect("editar_modulo", modulo_id=leccion.modulo.id)


@login_required
@user_passes_test(lambda u: u.perfil.rol == "INSTRUCTOR")
def eliminar_leccion(request, leccion_id):
    leccion = get_object_or_404(Leccion, id=leccion_id)
    titulo = leccion.titulo
    modulo_id = leccion.modulo.id

    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"ELIMINAR_LECCION: {titulo}",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    leccion.delete()
    messages.success(request, f'Lección "{titulo}" eliminada correctamente')
    return redirect("editar_modulo", modulo_id=modulo_id)


@login_required
def ver_leccion(request, leccion_id):
    leccion = get_object_or_404(Leccion, id=leccion_id)
    progreso, created = ProgresoUsuario.objects.get_or_create(
        usuario=request.user, leccion=leccion
    )

    total_puntos = sum(pregunta.puntos for pregunta in leccion.preguntas.all())

    lecciones = Leccion.objects.filter(modulo=leccion.modulo).order_by("orden")
    lecciones_lista = list(lecciones)
    idx = lecciones_lista.index(leccion) if leccion in lecciones_lista else -1

    leccion_anterior = lecciones_lista[idx - 1] if idx > 0 else None
    leccion_siguiente = lecciones_lista[idx + 1] if idx < len(lecciones_lista) - 1 else None

    modulo_completado = False
    modal_mostrado = False
    puntos_obtenidos = 0
    total_puntos_modulo = 0
    porcentaje_modulo = 0

    if request.method == "POST":
        if leccion.preguntas.exists():
            puntaje_total = 0
            todas_correctas = True

            for pregunta in leccion.preguntas.all():
                respuesta = request.POST.get(f"pregunta_{pregunta.id}", "")
                if respuesta and respuesta.lower().strip() == pregunta.respuesta_correcta.lower().strip():
                    puntaje_total += pregunta.puntos
                else:
                    todas_correctas = False

            if todas_correctas:
                progreso.completado = True
                progreso.puntaje = puntaje_total
                progreso.completado_en = timezone.now()
                progreso.save()
                messages.success(request, f"Lección completada! Puntaje: {puntaje_total}")
            else:
                progreso.puntaje = puntaje_total
                progreso.save()
                messages.warning(request, f"Puntaje obtenido: {puntaje_total}. Algunas respuestas son incorrectas.")
        else:
            progreso.completado = True
            progreso.completado_en = timezone.now()
            progreso.save()
            messages.success(request, "Lección marcada como completada")

        # Verificar si el módulo está completo
        todas_lecciones = leccion.modulo.lecciones.all()
        todas_completadas = True
        puntos_modulo = 0
        puntos_maximos = 0

        for l in todas_lecciones:
            p = ProgresoUsuario.objects.filter(usuario=request.user, leccion=l).first()
            if not p or not p.completado:
                todas_completadas = False
            if p:
                puntos_modulo += p.puntaje
            # Calcular puntos máximos del módulo
            for pg in l.preguntas.all():
                puntos_maximos += pg.puntos

        total_puntos_modulo = puntos_maximos
        puntos_obtenidos = puntos_modulo
        porcentaje_modulo = int((puntos_modulo / puntos_maximos * 100)) if puntos_maximos > 0 else 0
        modulo_completado = todas_completadas

        if modulo_completado:
            messages.success(request, f"FELICIDADES! Has completado el módulo {leccion.modulo.titulo}!")

        return redirect("ver_leccion", leccion_id=leccion.id)

    # Verificar si el módulo ya estaba completo antes
    todas_lecciones = leccion.modulo.lecciones.all()
    todas_completadas = True
    puntos_modulo = 0
    puntos_maximos = 0

    for l in todas_lecciones:
        p = ProgresoUsuario.objects.filter(usuario=request.user, leccion=l).first()
        if not p or not p.completado:
            todas_completadas = False
        if p:
            puntos_modulo += p.puntaje
        for pg in l.preguntas.all():
            puntos_maximos += pg.puntos

    total_puntos_modulo = puntos_maximos
    puntos_obtenidos = puntos_modulo
    porcentaje_modulo = int((puntos_modulo / puntos_maximos * 100)) if puntos_maximos > 0 else 0
    modulo_completado = todas_completadas

    context = {
        "leccion": leccion,
        "progreso": progreso,
        "total_puntos": total_puntos,
        "leccion_anterior": leccion_anterior,
        "leccion_siguiente": leccion_siguiente,
        "modulo_completado": modulo_completado,
        "puntos_obtenidos": puntos_obtenidos,
        "total_puntos_modulo": total_puntos_modulo,
        "porcentaje_modulo": porcentaje_modulo,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "lesson_detail.html", context)

@login_required
def progreso_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)
    lecciones = modulo.lecciones.all().order_by("orden")

    progreso_lecciones = []
    total_puntos = 0
    puntos_obtenidos = 0

    for leccion in lecciones:
        progreso = ProgresoUsuario.objects.filter(
            usuario=request.user, leccion=leccion
        ).first()

        puntos_leccion = sum(p.puntos for p in leccion.preguntas.all())
        total_puntos += puntos_leccion

        if progreso and progreso.completado:
            puntos_obtenidos += progreso.puntaje

        progreso_lecciones.append(
            {
                "leccion": leccion,
                "completado": progreso.completado if progreso else False,
                "puntaje": progreso.puntaje if progreso else 0,
                "puntos_totales": puntos_leccion,
            }
        )

    porcentaje = (puntos_obtenidos / total_puntos * 100) if total_puntos > 0 else 0
    modulo_completado = porcentaje == 100

    context = {
        "modulo": modulo,
        "progreso_lecciones": progreso_lecciones,
        "puntos_obtenidos": puntos_obtenidos,
        "total_puntos": total_puntos,
        "porcentaje": int(porcentaje),
        "modulo_completado": modulo_completado,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "progreso_modulo.html", context)


# ============================================================
# RETOS
# ============================================================


@login_required
def listar_retos(request):
    retos = Reto.objects.all()
    categorias = Categoria.objects.all()

    evento_id = request.GET.get("evento")
    evento_actual = None
    if evento_id:
        evento_actual = get_object_or_404(Evento, id=evento_id)
        retos = retos.filter(eventos=evento_actual)

    if request.user.perfil.rol not in ["INSTRUCTOR", "ADMIN"]:
        retos = retos.filter(esta_oculto=False)

    retos_resueltos = (
        IntentoReto.objects.filter(usuario=request.user, es_correcto=True)
        .values_list("reto_id", flat=True)
        .distinct()
    )
    retos_resueltos_ids = list(retos_resueltos)

    categoria_id = request.GET.get("categoria")
    if categoria_id:
        retos = retos.filter(categoria_id=categoria_id)

    dificultad = request.GET.get("dificultad")
    if dificultad:
        retos = retos.filter(dificultad=dificultad)

    estado = request.GET.get("estado")
    if estado == "resuelto":
        retos = retos.filter(id__in=retos_resueltos_ids)
    elif estado == "pendiente":
        retos = retos.exclude(id__in=retos_resueltos_ids)

    retos_resueltos_count = len(retos_resueltos_ids)
    retos_pendientes_count = (
        retos.count() - retos_resueltos_count if estado == "" else 0
    )
    porcentaje_completado = (
        int((retos_resueltos_count / retos.count() * 100)) if retos.count() > 0 else 0
    )

    context = {
        "retos": retos,
        "categorias": categorias,
        "retos_resueltos_ids": retos_resueltos_ids,
        "retos_resueltos_count": retos_resueltos_count,
        "retos_pendientes_count": retos_pendientes_count,
        "porcentaje_completado": porcentaje_completado,
        "evento_actual": evento_actual,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "challenge_list.html", context)


@login_required
def detalle_reto(request, reto_id):
    reto = get_object_or_404(Reto, id=reto_id)
    intento = IntentoReto.objects.filter(usuario=request.user, reto=reto).first()
    entorno = Entorno.objects.filter(usuario=request.user, reto=reto).first()

    if request.method == "POST" and "bandera" in request.POST:
        bandera_enviada = request.POST.get("bandera")
        es_correcto = bandera_enviada == reto.bandera

        if es_correcto:
            if not intento or not intento.es_correcto:
                IntentoReto.objects.create(
                    usuario=request.user,
                    reto=reto,
                    bandera_enviada=bandera_enviada,
                    es_correcto=True,
                )
                request.user.perfil.puntos += reto.puntos
                request.user.perfil.save()

                RegistroAuditoria.objects.create(
                    usuario=request.user,
                    accion=f"RESOLVER_RETO: {reto.titulo} (+{reto.puntos} pts)",
                    direccion_ip=request.META.get("REMOTE_ADDR"),
                )

                messages.success(request, f"¡Correcto! Has ganado {reto.puntos} puntos")
            else:
                messages.info(request, "Ya habias resuelto este reto anteriormente")
        else:
            messages.error(request, "Bandera incorrecta. Intenta de nuevo")

        return redirect("detalle_reto", reto_id=reto.id)

    return render(
        request,
        "challenge_detail.html",
        {
            "reto": reto,
            "intento": intento,
            "entorno": entorno,
        },
    )


@login_required
@user_passes_test(lambda u: u.perfil.rol in ["INSTRUCTOR", "ADMIN"])
def crear_reto(request):
    if request.method == "POST":
        reto = Reto.objects.create(
            titulo=request.POST.get("titulo"),
            descripcion=request.POST.get("descripcion"),
            categoria_id=request.POST.get("categoria"),
            dificultad=request.POST.get("dificultad"),
            puntos=request.POST.get("puntos"),
            bandera=request.POST.get("bandera"),
            pista=request.POST.get("pista", ""),
            creado_por=request.user,
        )

        archivos = request.FILES.getlist("archivos")
        for archivo in archivos:
            RecursoReto.objects.create(reto=reto, titulo=archivo.name, archivo=archivo)

        if request.POST.get("habilitar_docker") == "true":
            reto.tiene_docker = True
            if request.FILES.get("dockerfile_file"):
                dockerfile = request.FILES["dockerfile_file"]
                reto.dockerfile = dockerfile.read().decode("utf-8")
            elif request.POST.get("dockerfile_texto"):
                reto.dockerfile = request.POST.get("dockerfile_texto")
            reto.save()

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"CREAR_RETO: {reto.titulo}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, f'Reto "{reto.titulo}" creado exitosamente')
        return redirect("detalle_reto", reto_id=reto.id)

    categorias = Categoria.objects.all()
    return render(request, "challenge_create.html", {"categorias": categorias})


@login_required
@user_passes_test(lambda u: u.perfil.rol in ["INSTRUCTOR", "ADMIN"])
def editar_reto(request, reto_id):
    reto = get_object_or_404(Reto, id=reto_id)

    if request.method == "POST":
        reto.titulo = request.POST.get("titulo")
        reto.descripcion = request.POST.get("descripcion")
        reto.categoria_id = request.POST.get("categoria")
        reto.dificultad = request.POST.get("dificultad")
        reto.puntos = request.POST.get("puntos")
        reto.bandera = request.POST.get("bandera")
        reto.pista = request.POST.get("pista", "")

        if request.POST.get("habilitar_docker") == "true":
            reto.tiene_docker = True
            if request.POST.get("dockerfile_texto"):
                reto.dockerfile = request.POST.get("dockerfile_texto")
        else:
            reto.tiene_docker = False
            reto.dockerfile = ""

        reto.save()

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"EDITAR_RETO: {reto.titulo}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, "Reto actualizado correctamente")
        return redirect("detalle_reto", reto_id=reto.id)

    categorias = Categoria.objects.all()
    return render(
        request, "challenge_edit.html", {"reto": reto, "categorias": categorias}
    )


@login_required
@user_passes_test(lambda u: u.perfil.rol in ["ADMIN", "INSTRUCTOR"])
def eliminar_reto(request, reto_id):
    reto = get_object_or_404(Reto, id=reto_id)
    titulo = reto.titulo

    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"ELIMINAR_RETO: {titulo}",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    reto.delete()
    messages.success(request, "Reto eliminado correctamente")
    return redirect("listar_retos")


# ============================================================
# ENTORNOS
# ============================================================


@login_required
def iniciar_entorno(request, reto_id):
    reto = get_object_or_404(Reto, id=reto_id)

    entorno, created = Entorno.objects.get_or_create(
        usuario=request.user, reto=reto, defaults={"estado": "DETENIDO"}
    )

    if entorno.estado == "EJECUTANDO":
        messages.warning(request, "Ya tienes un entorno activo para este reto")
        return redirect("detalle_reto", reto_id=reto.id)

    if not reto.dockerfile:
        messages.error(request, "Este reto no tiene Dockerfile configurado")
        return redirect("detalle_reto", reto_id=reto.id)

    try:
        try:
            import subprocess

            result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
            if result.returncode != 0:
                messages.error(request, f"Docker no está accesible: {result.stderr}")
                return redirect("detalle_reto", reto_id=reto.id)
        except Exception as e:
            messages.error(request, f"Error al ejecutar docker: {str(e)}")
            return redirect("detalle_reto", reto_id=reto.id)

        client = docker.from_env()

        dockerfiles_dir = os.path.join(settings.BASE_DIR, "dockerfiles")
        os.makedirs(dockerfiles_dir, exist_ok=True)

        dockerfile_path = os.path.join(
            dockerfiles_dir, f"Dockerfile_{reto.id}_{request.user.id}.txt"
        )
        with open(dockerfile_path, "w") as f:
            f.write(reto.dockerfile)

        image_name = f"cyberquest_reto_{reto.id}_{request.user.id}"

        try:
            image, logs = client.images.build(
                path=dockerfiles_dir,
                dockerfile=os.path.basename(dockerfile_path),
                tag=image_name,
                rm=True,
            )
        except docker.errors.BuildError as e:
            messages.error(request, f"Error al construir imagen: {str(e)}")
            entorno.estado = "ERROR"
            entorno.save()
            return redirect("detalle_reto", reto_id=reto.id)

        container_name = f"reto_{reto.id}_user_{request.user.id}_{uuid.uuid4().hex[:8]}"

        container = client.containers.run(
            image_name,
            detach=True,
            remove=True,
            name=container_name,
            ports={"80/tcp": None},
            mem_limit="512m",
        )

        container.reload()

        ports = container.attrs["NetworkSettings"]["Ports"]
        if ports and "80/tcp" in ports and ports["80/tcp"] and ports["80/tcp"]:
            port = ports["80/tcp"][0]["HostPort"]
            url = f"http://localhost:{port}"
        else:
            url = "No se pudo obtener el puerto - el contenedor no expone el puerto 80"

        entorno.id_contenedor = container.id
        entorno.estado = "EJECUTANDO"
        entorno.iniciado_en = timezone.now()
        entorno.configuracion_vpn = url
        entorno.save()

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"INICIAR_ENTORNO_DOCKER: {reto.titulo}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, f"Entorno iniciado! Accede en: {url}")

    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")
        messages.error(request, f"Detalle: {traceback.format_exc()[:500]}")
        entorno.estado = "ERROR"
        entorno.save()

    return redirect("detalle_reto", reto_id=reto.id)


@login_required
def detener_entorno(request, entorno_id):
    entorno = get_object_or_404(Entorno, id=entorno_id, usuario=request.user)
    entorno.estado = "DETENIDO"
    entorno.save()

    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"DETENER_ENTORNO_DOCKER: {entorno.reto.titulo}",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    messages.success(request, "Entorno detenido")
    return redirect("detalle_reto", reto_id=entorno.reto.id)


# ============================================================
# RANKINGS
# ============================================================

@login_required
def ranking_individual(request):
    competencias = (
        Perfil.objects.filter(esta_bloqueado=False, rol="ESTUDIANTE")
        .select_related("usuario")
        .order_by("-puntos")
    )

    total_retos = Reto.objects.filter(esta_oculto=False).count()

    for competidor in competencias:
        competidor.retos_completados = IntentoReto.objects.filter(
            usuario=competidor.usuario, es_correcto=True
        ).count()

        competidor.progreso_porcentaje = (
            (competidor.retos_completados / total_retos * 100) if total_retos > 0 else 0
        )

        equipo = competidor.usuario.equipos.first()
        competidor.equipo_nombre = equipo.nombre if equipo else None

    total_competidores = competencias.count()
    total_puntos_competidores = (
        competencias.aggregate(Sum("puntos"))["puntos__sum"] or 0
    )
    total_retos_resueltos = IntentoReto.objects.filter(
        usuario__perfil__rol="ESTUDIANTE", es_correcto=True
    ).count()

    mi_posicion = competencias.filter(puntos__gt=request.user.perfil.puntos).count() + 1

    niveles = {
        "Principiante": competencias.filter(puntos__lt=500).count(),
        "Intermedio": competencias.filter(puntos__gte=500, puntos__lt=1000).count(),
        "Avanzado": competencias.filter(puntos__gte=1000, puntos__lt=2000).count(),
        "Experto": competencias.filter(puntos__gte=2000).count(),
    }

    nivel_data = {"labels": list(niveles.keys()), "values": list(niveles.values())}

    top10 = competencias[:10]
    top10_data = {
        "labels": [c.usuario.username for c in top10],
        "values": [c.puntos for c in top10],
    }

    hoy = datetime.now().date()
    
    # RF-38: Datos de evolucion del usuario actual (individual)
    puntos_usuario_semanales = []
    for semana in range(4):
        fecha_inicio = hoy - timedelta(days=(3 - semana) * 7)
        fecha_fin = fecha_inicio + timedelta(days=7)
        puntos_semana = IntentoReto.objects.filter(
            usuario=request.user,
            es_correcto=True,
            intentado_en__date__range=[fecha_inicio, fecha_fin],
        ).aggregate(Sum("reto__puntos"))["reto__puntos__sum"] or 0
        puntos_usuario_semanales.append(puntos_semana)

    mi_evolution_data = {
        "labels": ["Semana 1", "Semana 2", "Semana 3", "Semana 4"],
        "values": puntos_usuario_semanales,
    }

    # Evolucion de los Top 5
    evolution_datasets = []
    for i, competidor in enumerate(top10[:5]):
        puntos_semanales = []
        for semana in range(4):
            fecha_inicio = hoy - timedelta(days=(3 - semana) * 7)
            fecha_fin = fecha_inicio + timedelta(days=7)
            puntos_semana = (
                IntentoReto.objects.filter(
                    usuario=competidor.usuario,
                    es_correcto=True,
                    intentado_en__date__range=[fecha_inicio, fecha_fin],
                ).aggregate(Sum("reto__puntos"))["reto__puntos__sum"]
                or 0
            )
            puntos_semanales.append(puntos_semana)

        evolution_datasets.append(
            {
                "label": competidor.usuario.username,
                "data": puntos_semanales,
                "borderColor": f"hsl({i * 60}, 70%, 50%)",
                "fill": False,
                "tension": 0.4,
            }
        )

    evolution_data = {
        "labels": ["Semana 1", "Semana 2", "Semana 3", "Semana 4"],
        "datasets": evolution_datasets,
    }

    difficulty_data = {
        "labels": ["Principiante", "Intermedio", "Avanzado"],
        "values": [
            IntentoReto.objects.filter(
                usuario__perfil__rol="ESTUDIANTE",
                es_correcto=True,
                reto__dificultad="PRINCIPIANTE",
            ).count(),
            IntentoReto.objects.filter(
                usuario__perfil__rol="ESTUDIANTE",
                es_correcto=True,
                reto__dificultad="INTERMEDIO",
            ).count(),
            IntentoReto.objects.filter(
                usuario__perfil__rol="ESTUDIANTE",
                es_correcto=True,
                reto__dificultad="AVANZADO",
            ).count(),
        ],
    }

    context = {
        "competencias": competencias,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
        "total_competidores": total_competidores,
        "total_puntos_competidores": total_puntos_competidores,
        "total_retos_resueltos": total_retos_resueltos,
        "mi_posicion": mi_posicion,
        "nivel_data": json.dumps(nivel_data),
        "top10_data": json.dumps(top10_data),
        "evolution_data": json.dumps(evolution_data),
        "difficulty_data": json.dumps(difficulty_data),
        "mi_evolution_data": json.dumps(mi_evolution_data),  # RF-38
    }

    return render(request, "ranking_individual.html", context)

@login_required
def ranking_equipos(request):
    equipos = Equipo.objects.annotate(
        retos_resueltos=Count(
            "miembros__intentoreto",
            filter=Q(miembros__intentoreto__es_correcto=True),
            distinct=True,
        )
    ).order_by("-puntos")

    total_retos = Reto.objects.filter(esta_oculto=False).count()

    for equipo in equipos:
        equipo.progreso_porcentaje = (
            (equipo.retos_resueltos / total_retos * 100) if total_retos > 0 else 0
        )

    total_equipos = equipos.count()
    # CORREGIDO: sin paréntesis porque es una propiedad
    total_miembros = sum(e.cantidad_miembros for e in equipos)
    total_puntos_equipos = equipos.aggregate(Sum("puntos"))["puntos__sum"] or 0

    mi_equipo = request.user.equipos.first() or request.user.equipos_liderados.first()
    mi_equipo_posicion = None
    if mi_equipo:
        for i, equipo in enumerate(equipos):
            if equipo.id == mi_equipo.id:
                mi_equipo_posicion = i + 1
                break

    tamano_data = {
        "labels": [
            "Pequeños (1-3 miembros)",
            "Medianos (4-6 miembros)",
            "Grandes (7+ miembros)",
        ],
        "values": [
            sum(1 for e in equipos if e.cantidad_miembros <= 3),
            sum(1 for e in equipos if 4 <= e.cantidad_miembros <= 6),
            sum(1 for e in equipos if e.cantidad_miembros >= 7),
        ],
    }

    top10_equipos = equipos[:10]
    top10_equipos_data = {
        "labels": [
            e.nombre[:15] + ("..." if len(e.nombre) > 15 else "") for e in top10_equipos
        ],
        "values": [e.puntos for e in top10_equipos],
    }

    hoy = datetime.now().date()
    semanas = ["Semana 1", "Semana 2", "Semana 3", "Semana 4"]
    evolucion_datasets = []

    for i, equipo in enumerate(top10_equipos[:5]):
        puntos_semanales = []
        miembros_ids = [equipo.lider.id] + list(
            equipo.miembros.values_list("id", flat=True)
        )

        for semana in range(4):
            fecha_inicio = hoy - timedelta(days=(3 - semana) * 7)
            fecha_fin = fecha_inicio + timedelta(days=7)
            puntos_semana = (
                IntentoReto.objects.filter(
                    usuario_id__in=miembros_ids,
                    es_correcto=True,
                    intentado_en__date__range=[fecha_inicio, fecha_fin],
                ).aggregate(Sum("reto__puntos"))["reto__puntos__sum"]
                or 0
            )
            puntos_semanales.append(puntos_semana)

        evolucion_datasets.append(
            {
                "label": equipo.nombre[:20],
                "data": puntos_semanales,
                "borderColor": f"hsl({i * 72}, 70%, 55%)",
                "backgroundColor": "transparent",
                "fill": False,
                "tension": 0.4,
                "pointRadius": 4,
                "pointHoverRadius": 6,
            }
        )

    evolucion_equipos_data = {"labels": semanas, "datasets": evolucion_datasets}

    dificultad_equipos_data = {
        "labels": ["Principiante", "Intermedio", "Avanzado"],
        "values": [
            IntentoReto.objects.filter(
                usuario__in=[
                    u for e in equipos for u in [e.lider] + list(e.miembros.all())
                ],
                es_correcto=True,
                reto__dificultad="PRINCIPIANTE",
            ).count(),
            IntentoReto.objects.filter(
                usuario__in=[
                    u for e in equipos for u in [e.lider] + list(e.miembros.all())
                ],
                es_correcto=True,
                reto__dificultad="INTERMEDIO",
            ).count(),
            IntentoReto.objects.filter(
                usuario__in=[
                    u for e in equipos for u in [e.lider] + list(e.miembros.all())
                ],
                es_correcto=True,
                reto__dificultad="AVANZADO",
            ).count(),
        ],
    }

    context = {
        "equipos": equipos,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
        "total_equipos": total_equipos,
        "total_miembros": total_miembros,
        "total_puntos_equipos": total_puntos_equipos,
        "mi_equipo": mi_equipo,
        "mi_equipo_posicion": mi_equipo_posicion,
        "tamano_data": json.dumps(tamano_data),
        "top10_equipos_data": json.dumps(top10_equipos_data),
        "evolucion_equipos_data": json.dumps(evolucion_equipos_data),
        "dificultad_equipos_data": json.dumps(dificultad_equipos_data),
    }

    return render(request, "ranking_equipos.html", context)


# ============================================================
# ASISTENTE IA
# ============================================================

from .ia_ctf import obtener_respuesta


@login_required
def consultar_asistente(request):
    config = ConfiguracionIA.objects.first()
    ia_habilitado = config.asistente_activo if config else True

    if request.method == "POST":
        if not ia_habilitado:
            return JsonResponse(
                {
                    "success": False,
                    "message": "El asistente IA ha sido deshabilitado por el administrador.",
                }
            )

        pregunta = request.POST.get("pregunta")
        if not pregunta:
            return JsonResponse(
                {"success": False, "message": "Por favor escribe una pregunta."}
            )

        respuesta = obtener_respuesta(request.user, pregunta)
        ConsultaIA.objects.create(
            usuario=request.user, pregunta=pregunta, respuesta=respuesta
        )
        return JsonResponse({"success": True, "message": respuesta})

    consultas = ConsultaIA.objects.filter(usuario=request.user).order_by("-creado_en")[
        :10
    ]
    return render(
        request,
        "ai_assistant.html",
        {"consultas": consultas, "ia_habilitado": ia_habilitado},
    )

# ============================================================
# EVENTOS
# ============================================================
@login_required
def listar_eventos(request):
    eventos = Evento.objects.all().order_by("-fecha_inicio")
    now = timezone.now()
    rol = request.user.perfil.rol
    buscar = request.GET.get("buscar", "")
    estado = request.GET.get("estado", "")

    # BUSCADOR POR NOMBRE - PARA TODOS LOS ROLES
    if buscar:
        eventos = eventos.filter(nombre__icontains=buscar)

    if rol == "ESTUDIANTE":
        # Procesar eventos para el estudiante
        for evento in eventos:
            evento.esta_inscrito = evento.participantes.filter(
                id=request.user.id
            ).exists()

            if evento.esta_inscrito:
                retos_resueltos = IntentoReto.objects.filter(
                    usuario=request.user, reto__in=evento.retos.all(), es_correcto=True
                )
                evento.puntuacion_usuario = sum(r.reto.puntos for r in retos_resueltos)
                evento.retos_resueltos = retos_resueltos.count()

        # Filtros personales para estudiante
        if estado == "inscrito":
            eventos = [e for e in eventos if hasattr(e, 'esta_inscrito') and e.esta_inscrito]
        elif estado == "activo":
            eventos = [e for e in eventos if e.fecha_inicio <= now <= e.fecha_fin]
        elif estado == "proximos":
            eventos = [e for e in eventos if e.fecha_inicio > now]
        elif estado == "finalizados":
            eventos = [e for e in eventos if e.fecha_fin < now]

        # Estadisticas para el estudiante
        eventos_inscritos = len(
            [
                e
                for e in Evento.objects.all()
                if e.participantes.filter(id=request.user.id).exists()
            ]
        )
        eventos_participando = len(
            [
                e
                for e in Evento.objects.all()
                if e.esta_inscrito(request.user)
                and e.fecha_inicio <= now <= e.fecha_fin
            ]
        )
        eventos_finalizados = len(
            [
                e
                for e in Evento.objects.all()
                if e.esta_inscrito(request.user) and e.fecha_fin < now
            ]
        )

        context = {
            "eventos": eventos,
            "now": now,
            "total_eventos": Evento.objects.count(),
            "eventos_inscritos": eventos_inscritos,
            "eventos_participando": eventos_participando,
            "eventos_finalizados": eventos_finalizados,
            "perfil": request.user.perfil,
            "rol": rol,
            "buscar": buscar,
        }

    else:
        # INSTRUCTOR o ADMIN - con filtros de gestion
        if estado == "activo":
            eventos = eventos.filter(fecha_inicio__lte=now, fecha_fin__gte=now)
        elif estado == "inactivo":
            eventos = eventos.filter(fecha_inicio__gt=now)
        elif estado == "finalizado":
            eventos = eventos.filter(fecha_fin__lt=now)

        # Para instructor/admin, tambien marcamos si el usuario actual esta inscrito (opcional)
        for evento in eventos:
            evento.esta_inscrito = evento.participantes.filter(
                id=request.user.id
            ).exists()

        context = {
            "eventos": eventos,
            "now": now,
            "perfil": request.user.perfil,
            "rol": rol,
            "buscar": buscar,
            "estado_filtro": estado,
        }

    return render(request, "event_list.html", context)


@login_required
def detalle_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)

    evento.esta_inscrito = evento.participantes.filter(id=request.user.id).exists()

    retos_resueltos_ids = []
    retos_resueltos_count = 0
    puntos_obtenidos = 0
    total_retos = evento.retos.count()
    total_puntos = sum(r.puntos for r in evento.retos.all())
    porcentaje = 0

    if evento.esta_inscrito and request.user.perfil.rol == "ESTUDIANTE":
        retos_resueltos = IntentoReto.objects.filter(
            usuario=request.user, reto__in=evento.retos.all(), es_correcto=True
        )
        retos_resueltos_ids = list(
            retos_resueltos.values_list("reto_id", flat=True).distinct()
        )
        retos_resueltos_count = len(retos_resueltos_ids)
        puntos_obtenidos = sum(r.reto.puntos for r in retos_resueltos)
        porcentaje = (
            int((retos_resueltos_count / total_retos * 100)) if total_retos > 0 else 0
        )

    context = {
        "evento": evento,
        "now": timezone.now(),
        "retos_resueltos_ids": retos_resueltos_ids,
        "retos_resueltos_count": retos_resueltos_count,
        "puntos_obtenidos": puntos_obtenidos,
        "total_retos": total_retos,
        "total_puntos": total_puntos,
        "porcentaje": porcentaje,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "event_detail.html", context)


@login_required
def inscribirse_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)

    if request.method == "POST":
        if evento.participantes.filter(id=request.user.id).exists():
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "message": "Ya estás inscrito en este evento"}
                )
            else:
                messages.warning(request, "Ya estás inscrito en este evento")
                return redirect("detalle_evento", evento_id=evento.id)

        evento.participantes.add(request.user)

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"INSCRIBIRSE_EVENTO: {evento.nombre}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "message": f'Te has unido al evento "{evento.nombre}"',
                }
            )
        else:
            messages.success(request, f'Te has inscrito al evento "{evento.nombre}"')
            return redirect("detalle_evento", evento_id=evento.id)

    return redirect("detalle_evento", evento_id=evento.id)


@login_required
@user_passes_test(lambda u: u.perfil.rol == "INSTRUCTOR")
def crear_evento(request):
    if request.method == "POST":
        evento = Evento.objects.create(
            nombre=request.POST.get("nombre"),
            descripcion=request.POST.get("descripcion"),
            fecha_inicio=request.POST.get("fecha_inicio"),
            fecha_fin=request.POST.get("fecha_fin"),
            reglas=request.POST.get("reglas", ""),
            esta_activo=request.POST.get("esta_activo") == "on",
        )

        retos_ids = request.POST.getlist("retos")
        evento.retos.set(retos_ids)

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"CREAR_EVENTO: {evento.nombre}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, f'Evento "{evento.nombre}" creado exitosamente')
        return redirect("detalle_evento", evento_id=evento.id)

    retos = Reto.objects.filter(esta_oculto=False)
    context = {
        "retos": retos,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "event_create.html", context)


@login_required
@user_passes_test(lambda u: u.perfil.rol == "INSTRUCTOR")
def editar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)

    if request.method == "POST":
        evento.nombre = request.POST.get("nombre")
        evento.descripcion = request.POST.get("descripcion")
        evento.fecha_inicio = request.POST.get("fecha_inicio")
        evento.fecha_fin = request.POST.get("fecha_fin")
        evento.reglas = request.POST.get("reglas", "")
        evento.esta_activo = request.POST.get("esta_activo") == "on"
        evento.retos.set(request.POST.getlist("retos"))
        evento.save()

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"EDITAR_EVENTO: {evento.nombre}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, f'Evento "{evento.nombre}" actualizado correctamente')
        return redirect("listar_eventos")

    retos = Reto.objects.filter(esta_oculto=False)
    context = {
        "evento": evento,
        "retos": retos,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "event_edit.html", context)


@login_required
@user_passes_test(lambda u: u.perfil.rol == "INSTRUCTOR")
def eliminar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    nombre = evento.nombre

    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"ELIMINAR_EVENTO: {nombre}",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    evento.delete()
    messages.success(request, f'Evento "{nombre}" eliminado correctamente')
    return redirect("listar_eventos")


# ============================================================
# AUDITORÍA
# ============================================================


@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def auditoria(request):
    registros = (
        RegistroAuditoria.objects.all().select_related("usuario").order_by("-timestamp")
    )

    tipo_accion = request.GET.get("tipo")
    if tipo_accion:
        registros = registros.filter(accion__icontains=tipo_accion)

    usuario_id = request.GET.get("usuario")
    if usuario_id:
        registros = registros.filter(usuario_id=usuario_id)

    total_registros = registros.count()

    tipos_acciones = (
        RegistroAuditoria.objects.values("accion")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    usuarios_activos = (
        RegistroAuditoria.objects.values("usuario__username", "usuario__id")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    hoy = timezone.now().date()
    acciones_hoy = RegistroAuditoria.objects.filter(timestamp__date=hoy).count()

    context = {
        "registros": registros,
        "total_registros": total_registros,
        "tipos_acciones": tipos_acciones,
        "usuarios_activos": usuarios_activos,
        "acciones_hoy": acciones_hoy,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "auditoria.html", context)


# ============================================================
# CONFIGURACIÓN IA (ADMIN)
# ============================================================

# ============================================================
# CONFIGURACIÓN IA (ADMIN)
# ============================================================


@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def configuracion_ia(request):
    # Obtener o crear la configuración
    config = ConfiguracionIA.objects.first()
    if not config:
        config = ConfiguracionIA.objects.create(asistente_activo=True)  # Sin limite_consultas

    if request.method == "POST":
        asistente_activo = request.POST.get("asistente_activo") == "on"
        # limite_consultas = request.POST.get("limite_consultas", 10)  # ELIMINADO

        config.asistente_activo = asistente_activo
        # config.limite_consultas_por_dia = limite_consultas  # ELIMINADO
        config.actualizado_por = request.user
        config.save()

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"CONFIGURACION_IA: {'Activado' if asistente_activo else 'Desactivado'}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )

        messages.success(request, "Configuración del Asistente IA actualizada correctamente")
        return redirect("configuracion_ia")

    context = {
        "config": config,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "configuracion_ia.html", context)


@login_required
def certificado(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)

    # Verificar si el usuario completó el módulo
    lecciones = modulo.lecciones.all()
    completado = True
    for leccion in lecciones:
        progreso = ProgresoUsuario.objects.filter(usuario=request.user, leccion=leccion, completado=True).first()
        if not progreso:
            completado = False
            break

    if not completado:
        messages.error(request, "Debes completar todas las lecciones del módulo para obtener el certificado.")
        return redirect('progreso_modulo', modulo_id=modulo.id)

    # Crear o obtener certificado
    certificado, created = Certificado.objects.get_or_create(
        usuario=request.user,
        modulo=modulo,
        defaults={'codigo': str(uuid.uuid4())}
    )

    context = {
        'certificado': certificado,
        'modulo': modulo,
        'usuario': request.user,
        'fecha': timezone.now(),
        'perfil': request.user.perfil,
        'rol': request.user.perfil.rol,
    }
    return render(request, 'certificado.html', context)




# ============================================================
# ACCIONES DE EQUIPOS (COMPLETAS)
# ============================================================

@login_required
def eliminar_equipo(request, equipo_id):
    """Eliminar equipo - Puede hacerlo: El líder del equipo o el administrador"""
    equipo = get_object_or_404(Equipo, id=equipo_id)

    # Verificar permisos
    es_admin = request.user.perfil.rol == "ADMIN"
    es_lider = request.user == equipo.lider

    if not (es_admin or es_lider):
        messages.error(request, "No tienes permiso para eliminar este equipo")
        return redirect("ver_equipo", equipo_id=equipo.id)

    nombre = equipo.nombre

    # Registrar en auditoría
    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"ELIMINAR_EQUIPO: {nombre} (ID:{equipo.id})",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    equipo.delete()
    messages.success(request, f'Equipo "{nombre}" eliminado correctamente')
    return redirect("listar_equipos")


@login_required
def editar_equipo(request, equipo_id):
    """
    Editar equipo - Puede hacerlo:
    - El líder del equipo
    - El administrador
    """
    equipo = get_object_or_404(Equipo, id=equipo_id)

    es_admin = request.user.perfil.rol == "ADMIN"
    es_lider = request.user == equipo.lider

    if not (es_admin or es_lider):
        messages.error(request, "No tienes permiso para editar este equipo")
        return redirect("ver_equipo", equipo_id=equipo.id)

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion", "")

        # Verificar que el nombre no exista (excepto el mismo equipo)
        if Equipo.objects.filter(nombre=nombre).exclude(id=equipo.id).exists():
            messages.error(request, "Ya existe un equipo con ese nombre")
        else:
            equipo.nombre = nombre
            equipo.descripcion = descripcion
            equipo.save()

            RegistroAuditoria.objects.create(
                usuario=request.user,
                accion=f"EDITAR_EQUIPO: {nombre} (ID:{equipo.id})",
                direccion_ip=request.META.get("REMOTE_ADDR"),
            )

            messages.success(request, f'Equipo "{nombre}" actualizado correctamente')
            return redirect("ver_equipo", equipo_id=equipo.id)

    return render(request, "team_edit.html", {"equipo": equipo})


@login_required
def expulsar_miembro(request, equipo_id, user_id):
    """
    Expulsar miembro del equipo - Puede hacerlo:
    - El líder del equipo
    - El administrador
    """
    equipo = get_object_or_404(Equipo, id=equipo_id)
    usuario_a_expulsar = get_object_or_404(User, id=user_id)

    es_admin = request.user.perfil.rol == "ADMIN"
    es_lider = request.user == equipo.lider

    # Verificar permisos
    if not (es_admin or es_lider):
        messages.error(request, "No tienes permiso para expulsar miembros")
        return redirect("ver_equipo", equipo_id=equipo.id)

    # No se puede expulsar al líder
    if usuario_a_expulsar == equipo.lider:
        messages.error(request, "No puedes expulsar al líder del equipo")
        return redirect("ver_equipo", equipo_id=equipo.id)

    # Verificar que sea miembro
    if usuario_a_expulsar not in equipo.miembros.all():
        messages.error(request, "El usuario no es miembro del equipo")
        return redirect("ver_equipo", equipo_id=equipo.id)

    # No te puedes expulsar a ti mismo (usa salir_equipo para eso)
    if usuario_a_expulsar == request.user and not es_admin:
        messages.error(request, "Usa 'Salir del equipo' si quieres abandonar el equipo")
        return redirect("ver_equipo", equipo_id=equipo.id)

    # Realizar expulsión
    equipo.miembros.remove(usuario_a_expulsar)

    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"EXPULSAR_MIEMBRO: {usuario_a_expulsar.username} del equipo {equipo.nombre} (ID:{equipo.id})",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    messages.success(request, f'{usuario_a_expulsar.username} ha sido expulsado del equipo "{equipo.nombre}"')

    # Si el admin expulsa a alguien, vuelve a la lista de equipos
    if es_admin:
        return redirect("listar_equipos")
    return redirect("ver_equipo", equipo_id=equipo.id)


@login_required
def salir_equipo(request, equipo_id):
    """
    Salir del equipo voluntariamente - Puede hacerlo:
    - Cualquier miembro (excepto el líder)
    """
    equipo = get_object_or_404(Equipo, id=equipo_id)

    # El líder no puede salir, debe eliminar el equipo o transferir liderazgo
    if request.user == equipo.lider:
        messages.error(request, "Eres el líder. No puedes salir. Elimina el equipo o transfiere el liderazgo.")
        return redirect("ver_equipo", equipo_id=equipo.id)

    # Verificar que sea miembro
    if request.user not in equipo.miembros.all():
        messages.error(request, "No eres miembro de este equipo")
        return redirect("listar_equipos")

    # Salir del equipo
    equipo.miembros.remove(request.user)

    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"SALIR_EQUIPO: {equipo.nombre} (ID:{equipo.id})",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    messages.success(request, f'Has salido del equipo "{equipo.nombre}"')
    return redirect("listar_equipos")


@login_required
def transferir_liderazgo(request, equipo_id, user_id):
    """Transferir liderazgo a otro miembro (solo líder)"""
    equipo = get_object_or_404(Equipo, id=equipo_id)
    nuevo_lider = get_object_or_404(User, id=user_id)

    # Solo el líder actual puede transferir
    if request.user != equipo.lider:
        messages.error(request, "Solo el líder puede transferir el liderazgo")
        return redirect("ver_equipo", equipo_id=equipo.id)

    # Verificar que el nuevo líder sea miembro
    if nuevo_lider not in equipo.miembros.all():
        messages.error(request, "El usuario no es miembro del equipo")
        return redirect("ver_equipo", equipo_id=equipo.id)

    # Transferir liderazgo
    equipo.lider = nuevo_lider
    equipo.save()

    # El antiguo líder sigue como miembro
    if request.user not in equipo.miembros.all():
        equipo.miembros.add(request.user)

    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"TRANSFERIR_LIDERAZGO: {nuevo_lider.username} en equipo {equipo.nombre}",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )

    messages.success(request, f'Liderazgo transferido a {nuevo_lider.username}')
    return redirect("ver_equipo", equipo_id=equipo.id)
@login_required
def equipo_reto_detalle(request, reto_id):
    reto = get_object_or_404(Reto, id=reto_id)

    # Obtener el equipo del usuario
    equipo = request.user.equipos.first() or request.user.equipos_liderados.first()

    if not equipo:
        messages.error(request, "No perteneces a ningún equipo")
        return redirect("listar_retos")

    # Verificar si el usuario ya resolvió el reto
    ya_resuelto = IntentoReto.objects.filter(usuario=request.user, reto=reto, es_correcto=True).exists()

    entorno = Entorno.objects.filter(usuario=request.user, reto=reto).first()

    if request.method == "POST":
        bandera_enviada = request.POST.get("bandera")
        es_correcto = bandera_enviada == reto.bandera

        if es_correcto:
            if not ya_resuelto:
                IntentoReto.objects.create(
                    usuario=request.user,
                    reto=reto,
                    bandera_enviada=bandera_enviada,
                    es_correcto=True,
                )
                request.user.perfil.puntos += reto.puntos
                request.user.perfil.save()

                # Sumar puntos al equipo
                equipo.puntos += reto.puntos
                equipo.save()

                messages.success(request, f"Correcto! Has ganado {reto.puntos} puntos para tu equipo")
            else:
                messages.info(request, "Ya habias resuelto este reto anteriormente")
            return redirect("equipo_reto_detalle", reto_id=reto.id)
        else:
            messages.error(request, "Bandera incorrecta. Intenta de nuevo")

    context = {
        "reto": reto,
        "equipo": equipo,
        "ya_resuelto": ya_resuelto,
        "entorno": entorno,
        "perfil": request.user.perfil,
        "rol": request.user.perfil.rol,
    }
    return render(request, "team_reto_detail.html", context)



@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def exportar_logs_pdf(request):
    """Exportar logs de auditoría a PDF con diseño profesional (RF-51)"""
    
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import io
    from django.http import HttpResponse
    
    # Obtener registros con filtros
    registros = RegistroAuditoria.objects.all().select_related('usuario').order_by('-timestamp')
    
    tipo_accion = request.GET.get('tipo')
    if tipo_accion:
        registros = registros.filter(accion__icontains=tipo_accion)
    
    usuario_id = request.GET.get('usuario')
    if usuario_id:
        registros = registros.filter(usuario_id=usuario_id)
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="cyberquest_auditoria.pdf"'
    
    # Crear buffer y documento
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Estilos personalizados
    styles = getSampleStyleSheet()
    
    # Estilo para título principal
    titulo_style = ParagraphStyle(
        'TituloStyle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#E10600'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=5
    )
    
    # Estilo para subtítulo
    subtitulo_style = ParagraphStyle(
        'SubtituloStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#6c6c7a'),
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    # Estilo para fecha
    fecha_style = ParagraphStyle(
        'FechaStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#333333'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    # Estilo para encabezados de tabla
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    
    # Estilo para celdas de tabla
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.black,
        alignment=TA_LEFT
    )
    
    # Construir contenido
    story = []
    
    # Título
    story.append(Paragraph("CYBERQUEST", titulo_style))
    story.append(Paragraph("Security Training Platform - Reporte de Auditoria", subtitulo_style))
    
    # Fecha
    fecha_text = f"Generado: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}  |  Total registros: {registros.count()}"
    story.append(Paragraph(fecha_text, fecha_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # Datos de la tabla
    data = []
    
    # Encabezados
    headers = ['FECHA Y HORA', 'USUARIO', 'ROL', 'ACCION', 'DIRECCION IP']
    data.append([Paragraph(h, header_style) for h in headers])
    
    # Contenido
    for log in registros[:500]:
        rol_usuario = log.usuario.perfil.rol if hasattr(log.usuario, 'perfil') else 'DESCONOCIDO'
        
        row = [
            Paragraph(log.timestamp.strftime("%d/%m/%Y %H:%M:%S"), cell_style),
            Paragraph(log.usuario.username, cell_style),
            Paragraph(rol_usuario, cell_style),
            Paragraph(log.accion[:70], cell_style),
            Paragraph(log.direccion_ip or "No registrada", cell_style),
        ]
        data.append(row)
    
    # Crear tabla
    table = Table(data, repeatRows=1)
    
    # Estilo de la tabla
    table.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E10600')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Filas alternadas
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROW BACKGROUND', (0, 2), (-1, -1), colors.HexColor('#f5f5f5')),
        
        # Bordes suaves
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#dddddd')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        
        # Alineaciones
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),
        
        # Padding
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    story.append(table)
    
    # Pie de página
    story.append(Spacer(1, 0.25 * inch))
    footer_text = """
    <font color="#888888" size="7">CyberQuest Security Training Platform - Reporte generado automaticamente</font>
    """
    footer_style = ParagraphStyle('FooterStyle', parent=styles['Normal'], alignment=TA_CENTER)
    story.append(Paragraph(footer_text, footer_style))
    
    # Construir PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    # Registrar acción
    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion="EXPORTAR_LOGS_PDF",
        direccion_ip=request.META.get("REMOTE_ADDR")
    )
    
    return response




from django.contrib.sessions.models import Session

def limpiar_sesiones_expiradas():
    """Elimina sesiones expiradas de la base de datos"""
    sesiones_expiradas = Session.objects.filter(expire_date__lt=timezone.now())
    count = sesiones_expiradas.count()
    sesiones_expiradas.delete()
    if count > 0:
        print(f"[LIMPIAR] {count} sesiones expiradas eliminadas")
    return count
@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def sesiones_activas(request):
    """Ver sesiones activas de usuarios (RF-52)"""
    
    from django.contrib.sessions.models import Session
    
    # Limpiar sesiones expiradas primero
    limpiar_sesiones_expiradas()
    
    # Solo sesiones activas (no expiradas)
    sesiones = Session.objects.filter(expire_date__gt=timezone.now())
    
    usuarios_activos = []
    for sesion in sesiones:
        data = sesion.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                tiempo_restante = sesion.expire_date - timezone.now()
                minutos_restantes = int(tiempo_restante.total_seconds() / 60)
                horas_restantes = int(minutos_restantes / 60)
                
                if horas_restantes > 24:
                    tiempo_str = f"{int(horas_restantes/24)} dias"
                elif horas_restantes > 0:
                    tiempo_str = f"{horas_restantes} horas"
                else:
                    tiempo_str = f"{minutos_restantes} min"
                
                usuarios_activos.append({
                    'username': user.username,
                    'rol': user.perfil.rol,
                    'tiempo_restante': tiempo_str,
                    'session_key': sesion.session_key,  # <--- ESTO ESTABA FALTANDO
                })
            except User.DoesNotExist:
                sesion.delete()
                pass
    
    total_sesiones = len(usuarios_activos)
    total_usuarios = Perfil.objects.filter(esta_bloqueado=False).count()
    
    context = {
        'sesiones': usuarios_activos,
        'total_sesiones': total_sesiones,
        'total_usuarios': total_usuarios,
        'perfil': request.user.perfil,
        'rol': request.user.perfil.rol,
    }
    
    return render(request, 'sesiones_activas.html', context)
@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def limpiar_sesiones(request):
    from django.contrib.sessions.models import Session
    count = Session.objects.filter(expire_date__lt=timezone.now()).count()
    Session.objects.filter(expire_date__lt=timezone.now()).delete()
    messages.success(request, f"Se eliminaron {count} sesiones expiradas")
    return redirect('sesiones_activas')
@login_required
@user_passes_test(lambda u: u.perfil.rol == "ADMIN")
def eliminar_sesion(request, session_key):
    """Eliminar una sesión específica (forzar cierre)"""
    from django.contrib.sessions.models import Session
    try:
        session = Session.objects.get(session_key=session_key)
        session.delete()
        messages.success(request, "Sesión eliminada correctamente")
    except Session.DoesNotExist:
        messages.error(request, "Sesión no encontrada")
    return redirect('sesiones_activas')

@login_required
def ver_modulo(request, modulo_id):
    """Ver detalles de un módulo"""
    modulo = get_object_or_404(Modulo, id=modulo_id)
    
    # Verificar permisos (solo ver módulos publicados o si es instructor/admin)
    if not modulo.esta_publicado and request.user.perfil.rol not in ['INSTRUCTOR', 'ADMIN']:
        messages.error(request, "Este módulo no está disponible")
        return redirect('listar_modulos')
    
    # Obtener lecciones del módulo
    lecciones = modulo.lecciones.all().order_by('orden')
    
    # Si es estudiante, calcular progreso
    progreso = None
    if request.user.perfil.rol == 'ESTUDIANTE':
        lecciones_completadas = 0
        puntos_obtenidos = 0
        puntos_totales = 0
        
        for leccion in lecciones:
            prog = ProgresoUsuario.objects.filter(usuario=request.user, leccion=leccion).first()
            if prog and prog.completado:
                lecciones_completadas += 1
                puntos_obtenidos += prog.puntaje
            
            # Calcular puntos máximos de la lección
            puntos_leccion = sum(p.puntos for p in leccion.preguntas.all())
            puntos_totales += puntos_leccion
        
        porcentaje = int((lecciones_completadas / lecciones.count() * 100)) if lecciones.count() > 0 else 0
        
        progreso = {
            'lecciones_completadas': lecciones_completadas,
            'porcentaje': porcentaje,
            'puntos_obtenidos': puntos_obtenidos,
            'puntos_totales': puntos_totales,
        }
    
    context = {
        'modulo': modulo,
        'lecciones': lecciones,
        'progreso': progreso,
        'perfil': request.user.perfil,
        'rol': request.user.perfil.rol,
    }
    return render(request, 'modulo_detail.html', context)


@login_required
def historial_consultas(request):
    consultas = ConsultaIA.objects.filter(usuario=request.user).order_by('-creado_en')
    data = {
        'consultas': [{
            'pregunta': c.pregunta,
            'respuesta': c.respuesta,
            'fecha': c.creado_en.strftime('%d/%m/%Y %H:%M')
        } for c in consultas]
    }
    return JsonResponse(data)


# Agrega estas funciones al final de views.py

def handler404(request, exception):
    """Manejo de error 404 - Página no encontrada"""
    return render(request, '404.html', status=404)

def handler500(request):
    """Manejo de error 500 - Error interno del servidor"""
    return render(request, '500.html', status=500)

def handler403(request, exception):
    """Manejo de error 403 - Acceso denegado"""
    return render(request, '403.html', status=403)

# ============================================================
# GESTIÓN DE PREGUNTAS
# ============================================================

@login_required
@user_passes_test(lambda u: u.perfil.rol in ["INSTRUCTOR", "ADMIN"])
def agregar_pregunta(request):
    """Agregar una nueva pregunta a una lección"""
    if request.method == "POST":
        leccion_id = request.POST.get("leccion_id_pregunta")  # Cambiado: leccion_id_pregunta
        texto_pregunta = request.POST.get("texto_pregunta")
        respuesta_correcta = request.POST.get("respuesta_correcta")
        puntos = request.POST.get("puntos", 10)
        
        if not leccion_id or not texto_pregunta or not respuesta_correcta:
            messages.error(request, "Todos los campos son requeridos")
            return redirect("listar_modulos")
        
        # Obtener la lección ANTES de usarla
        leccion = get_object_or_404(Leccion, id=leccion_id)
        
        Pregunta.objects.create(
            leccion=leccion,
            texto_pregunta=texto_pregunta,
            respuesta_correcta=respuesta_correcta,
            puntos=puntos
        )
        
        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"CREAR_PREGUNTA: {texto_pregunta[:50]}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )
        
        messages.success(request, "Pregunta agregada correctamente")
        return redirect("editar_modulo", modulo_id=leccion.modulo.id)
    
    return redirect("listar_modulos")


@login_required
@user_passes_test(lambda u: u.perfil.rol in ["INSTRUCTOR", "ADMIN"])
def editar_pregunta(request, pregunta_id):
    """Editar una pregunta existente"""
    pregunta = get_object_or_404(Pregunta, id=pregunta_id)
    
    if request.method == "POST":
        texto_pregunta = request.POST.get("texto_pregunta")
        respuesta_correcta = request.POST.get("respuesta_correcta")
        puntos = request.POST.get("puntos", 10)
        
        if not texto_pregunta or not respuesta_correcta:
            messages.error(request, "Todos los campos son requeridos")
            return redirect("editar_modulo", modulo_id=pregunta.leccion.modulo.id)
        
        pregunta.texto_pregunta = texto_pregunta
        pregunta.respuesta_correcta = respuesta_correcta
        pregunta.puntos = puntos
        pregunta.save()
        
        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion=f"EDITAR_PREGUNTA: {texto_pregunta[:50]}",
            direccion_ip=request.META.get("REMOTE_ADDR"),
        )
        
        messages.success(request, "Pregunta actualizada correctamente")
        return redirect("editar_modulo", modulo_id=pregunta.leccion.modulo.id)
    
    return redirect("listar_modulos")


@login_required
@user_passes_test(lambda u: u.perfil.rol in ["INSTRUCTOR", "ADMIN"])
def eliminar_pregunta(request, pregunta_id):
    """Eliminar una pregunta"""
    pregunta = get_object_or_404(Pregunta, id=pregunta_id)
    modulo_id = pregunta.leccion.modulo.id
    texto_pregunta = pregunta.texto_pregunta[:50]
    
    RegistroAuditoria.objects.create(
        usuario=request.user,
        accion=f"ELIMINAR_PREGUNTA: {texto_pregunta}",
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )
    
    pregunta.delete()
    messages.success(request, "Pregunta eliminada correctamente")
    return redirect("editar_modulo", modulo_id=modulo_id)