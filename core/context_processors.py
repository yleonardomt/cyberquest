def global_context(request):
    if request.user.is_authenticated:
        return {
            'perfil': request.user.perfil,
            'rol': request.user.perfil.rol,
        }
    return {}