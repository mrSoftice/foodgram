import re
from collections import Counter

from django.conf import settings
from django.core.exceptions import ValidationError


def username_validation(username):
    if invalid_symbols := re.findall(settings.USERNAME_ANTIPATTERN, username):
        raise ValidationError(
            settings.USERNAME_WITH_BAD_SYMBOLS.format(
                ', '.join(', '.join(f'"{s}"' for s in invalid_symbols))
            )
        )
    return username


def no_repeating_elements_in_list(value, list_name='', field_name='id'):
    dublicate_ids = [
        id
        for id, count in Counter(item[field_name] for item in value).items()
        if count > 1
    ]
    if dublicate_ids:
        raise ValidationError(
            f'В поле "{list_name}" повторятся элементы {dublicate_ids}'
        )
    return value
