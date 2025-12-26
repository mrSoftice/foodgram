from hashids import Hashids

from foodgram.settings import BASE62_ALPHABET

_HASHIDS = Hashids(salt='foodgram', min_length=3)


def encode_base62(num):
    """Кодирует целое число в строку в системе Base62."""

    if num == 0:
        return BASE62_ALPHABET[0]
    base = len(BASE62_ALPHABET)
    encoded = []
    while num > 0:
        num, rem = divmod(num, base)
        encoded.append(BASE62_ALPHABET[rem])
    return ''.join(reversed(encoded))


def decode_base62(encoded_str):
    """Декодирует строку в системе Base62 обратно в целое число."""

    base = len(BASE62_ALPHABET)
    decoded = 0
    for char in encoded_str:
        decoded = decoded * base + BASE62_ALPHABET.index(char)
    return decoded


def encode_hashid(id):
    """Кодирует идентификатор в короткую строку с помощью Hashids."""
    return _HASHIDS.encode(id)


def decode_hashid(encoded_str):
    """
    Декодирует короткую строку обратно в идентификатор с помощью Hashids.
    Raises:
        ValueError: если код некорректный
    """
    decoded = _HASHIDS.decode(encoded_str)
    if not decoded:
        raise ValueError('Invalid short link code')
    return decoded[0]


def get_short_link(id, request):
    """Генерирует короткую ссылку на основе идентификатора."""
    encoded_id = encode_hashid(id)
    return request.build_absolute_uri(f'/s/{encoded_id}')


def get_id_from_short_link(code):
    """Получает идентификатор из короткой ссылки."""
    return decode_hashid(code)
