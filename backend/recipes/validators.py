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
