from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.conf.urls import handler404, handler500, handler403

# Agrega después de los imports
handler404 = "core.views.handler404"
handler500 = "core.views.handler500"
handler403 = "core.views.handler403"

urlpatterns = [
    # ============================================================
    # VISTAS PÚBLICAS
    # ============================================================
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("reset/", views.reset_password_request, name="reset"),
    path("reset/<str:token>/", views.reset_password_confirm, name="reset_confirm"),
    # ============================================================
    # DASHBOARD Y PERFIL (M1)
    # ============================================================
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.perfil_detalle, name="perfil_detalle"),
    path("profile/edit/", views.perfil_editar, name="perfil_editar"),
    # ============================================================
    # CRUD USUARIOS (ADMIN)
    # ============================================================
    path("users/", views.listar_usuarios, name="listar_usuarios"),
    path("users/create/", views.crear_usuario, name="crear_usuario"),
    path("users/<int:user_id>/edit/", views.editar_usuario, name="editar_usuario"),
    path(
        "users/<int:user_id>/delete/", views.eliminar_usuario, name="eliminar_usuario"
    ),
    path("users/<int:user_id>/block/", views.bloquear_usuario, name="bloquear_usuario"),
    # ============================================================
    # EQUIPOS (M2) - URLs LIMPIAS Y SIN DUPLICADOS
    # ============================================================
    path("teams/", views.listar_equipos, name="listar_equipos"),
    path("teams/create/", views.crear_equipo, name="crear_equipo"),
    path("teams/join/", views.unirse_equipo, name="unirse_equipo"),
    path("teams/<int:equipo_id>/", views.ver_equipo, name="ver_equipo"),
    path("teams/<int:equipo_id>/edit/", views.editar_equipo, name="editar_equipo"),
    path(
        "teams/<int:equipo_id>/delete/", views.eliminar_equipo, name="eliminar_equipo"
    ),
    path(
        "teams/<int:equipo_id>/kick/<int:user_id>/",
        views.expulsar_miembro,
        name="expulsar_miembro",
    ),
    path("teams/<int:equipo_id>/salir/", views.salir_equipo, name="salir_equipo"),
    path("teams/<int:equipo_id>/retos/", views.equipo_retos, name="equipo_retos"),
    path(
        "teams/<int:equipo_id>/enviar-bandera/",
        views.enviar_bandera_equipo,
        name="enviar_bandera_equipo",
    ),
    path(
        "teams/reto/<int:reto_id>/",
        views.equipo_reto_detalle,
        name="equipo_reto_detalle",
    ),
    # ============================================================
    # MÓDULOS Y APRENDIZAJE (M3)
    # ============================================================
    # ============================================================
    # MÓDULOS Y APRENDIZAJE (M3)
    # ============================================================
    path("modules/", views.listar_modulos, name="listar_modulos"),
    path("module/create/", views.crear_modulo, name="crear_modulo"),
    path("modulo/<int:modulo_id>/", views.ver_modulo, name="ver_modulo"),
    path("modulo/<int:modulo_id>/editar/", views.editar_modulo, name="editar_modulo"),
    path(
        "modulo/<int:modulo_id>/eliminar/",
        views.eliminar_modulo,
        name="eliminar_modulo",
    ),
    path(
        "modulo/<int:modulo_id>/progreso/",
        views.progreso_modulo,
        name="progreso_modulo",
    ),
    path(
        "modulo/<int:modulo_id>/leccion/agregar/",
        views.agregar_leccion,
        name="agregar_leccion",
    ),
    path("leccion/<int:leccion_id>/", views.ver_leccion, name="ver_leccion"),
    path(
        "leccion/<int:leccion_id>/editar/", views.editar_leccion, name="editar_leccion"
    ),
    path(
        "leccion/<int:leccion_id>/eliminar/",
        views.eliminar_leccion,
        name="eliminar_leccion",
    ),
    # AGREGAR ESTAS TRES LÍNEAS:
    path("pregunta/agregar/", views.agregar_pregunta, name="agregar_pregunta"),
    path(
        "pregunta/<int:pregunta_id>/editar/",
        views.editar_pregunta,
        name="editar_pregunta",
    ),
    path(
        "pregunta/<int:pregunta_id>/eliminar/",
        views.eliminar_pregunta,
        name="eliminar_pregunta",
    ),
    # ============================================================
    # RETOS CTF (M4)
    # ============================================================
    path("challenges/", views.listar_retos, name="listar_retos"),
    path("challenge/create/", views.crear_reto, name="crear_reto"),
    path("challenge/<int:reto_id>/", views.detalle_reto, name="detalle_reto"),
    path("challenge/<int:reto_id>/edit/", views.editar_reto, name="editar_reto"),
    path("challenge/<int:reto_id>/delete/", views.eliminar_reto, name="eliminar_reto"),
    # ============================================================
    # ENTORNOS DOCKER (M5)
    # ============================================================
    path(
        "environment/<int:reto_id>/start/",
        views.iniciar_entorno,
        name="iniciar_entorno",
    ),
    path(
        "environment/<int:entorno_id>/stop/",
        views.detener_entorno,
        name="detener_entorno",
    ),
    # ============================================================
    # RANKINGS (M7)
    # ============================================================
    path("ranking/individual/", views.ranking_individual, name="ranking_individual"),
    path("ranking/teams/", views.ranking_equipos, name="ranking_equipos"),
    # ============================================================
    # ASISTENTE IA (M9)
    # ============================================================
    path("ai/", views.consultar_asistente, name="consultar_asistente"),
    path("ai/historial/", views.historial_consultas, name="historial_consultas"),
    # ============================================================
    # EVENTOS CTF (M10)
    # ============================================================
    path("events/", views.listar_eventos, name="listar_eventos"),
    path("event/create/", views.crear_evento, name="crear_evento"),
    path("event/<int:evento_id>/", views.detalle_evento, name="detalle_evento"),
    path(
        "event/<int:evento_id>/join/",
        views.inscribirse_evento,
        name="inscribirse_evento",
    ),
    path("event/<int:evento_id>/editar/", views.editar_evento, name="editar_evento"),
    path(
        "event/<int:evento_id>/eliminar/", views.eliminar_evento, name="eliminar_evento"
    ),
    # ============================================================
    # AUDITORÍA (M7)
    # ============================================================
    path("auditoria/", views.auditoria, name="auditoria"),
    path("auditoria/exportar-pdf/", views.exportar_logs_pdf, name="exportar_logs_pdf"),
    path("sesiones-activas/", views.sesiones_activas, name="sesiones_activas"),
    path("sesiones/limpiar/", views.limpiar_sesiones, name="limpiar_sesiones"),
    path(
        "sesiones/eliminar/<str:session_key>/",
        views.eliminar_sesion,
        name="eliminar_sesion",
    ),
    # ============================================================
    # CERTIFICADOS
    # ============================================================
    path("certificado/<int:modulo_id>/", views.certificado, name="certificado"),
    # ============================================================
    # CONFIGURACIÓN IA
    # ============================================================
    path("configuracion-ia/", views.configuracion_ia, name="configuracion_ia"),
]

# Servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
