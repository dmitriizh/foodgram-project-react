from django.core.exceptions import ValidationError


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError("username не может быть 'me'")
    return value
