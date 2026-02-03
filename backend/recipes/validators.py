import re
from collections import Counter

from django.conf import settings
from django.core.exceptions import ValidationError

USERNAME_WITH_BAD_SYMBOLS = 'Поле "username" содержит недопустимые символы: {}'
FORBIDDEN_USERNAMES = getattr(settings, 'FORBIDDEN_USERNAMES', set())
USERNAME_ANTIPATTERN = getattr(settings, 'USERNAME_ANTIPATTERN', '')


def username_validation(username):
    if invalid_symbols := re.findall(USERNAME_ANTIPATTERN, username):
        raise ValidationError(
            USERNAME_WITH_BAD_SYMBOLS.format(
                ', '.join(list(dict.fromkeys(invalid_symbols)))
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
            f'В поле "{list_name}" повторятся элементы'
            f'{", ".join(dublicate_ids)}'
        )
    return value
