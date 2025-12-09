import re

from rest_framework.serializers import ValidationError

from foodgram.settings import FORBIDDEN_USERNAMES, USERNAME_ANTIPATTERN

USERNAME_NOT_ALLOWED = 'Запрещено использовать имя пользователя {}'
USERNAME_WITH_BAD_SYMBOLS = 'Поле "username" содержит недопустимые символы: {}'


def username_validation(username):
    if invalid_symbols := re.findall(USERNAME_ANTIPATTERN, username):
        raise ValidationError(USERNAME_WITH_BAD_SYMBOLS.format(invalid_symbols))
    if username in FORBIDDEN_USERNAMES:
        raise ValidationError(
            {'username': USERNAME_NOT_ALLOWED.format(username)}
        )
    return username


def validate_cooking_time(value):
    if value < 1:
        raise ValidationError(
            'Время приготовления должно быть больше или равно 1 минуте.'
        )
    return value


def list_is_not_empty(value, field_name=''):
    if not value:
        raise ValidationError(f'Поле "{field_name}" не должно быть пустым.')
    return value


def no_repeating_id_in_list(value, field_name=''):
    list_ids = [item['id'] for item in value]
    if len(list_ids) != len(set(list_ids)):
        raise ValidationError(
            f'Элементы в поле "{field_name}" не должны повторяться.'
        )
    return value
