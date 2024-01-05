import re

from django.core.exceptions import ValidationError


def validate_username(value):
    if not re.match(r'^[\w.@+-]+$', value):
        raise ValidationError(
            'Username содержит недопустимые символы'
        )
    return value
