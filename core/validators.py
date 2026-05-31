from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re

class MayusculaValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _('La contraseña debe contener al menos una letra mayúscula.'),
                code='password_no_mayuscula',
            )

class NumeroValidator:
    def validate(self, password, user=None):
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _('La contraseña debe contener al menos un número.'),
                code='password_no_numero',
            )

class SimboloValidator:
    def validate(self, password, user=None):
        if not re.search(r'[@$!%*#?&]', password):
            raise ValidationError(
                _('La contraseña debe contener al menos un símbolo (@$!%*#?&).'),
                code='password_no_simbolo',
            )