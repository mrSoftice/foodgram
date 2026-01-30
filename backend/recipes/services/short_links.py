from hashids import Hashids

_HASHIDS = Hashids(salt='foodgram', min_length=3)


def encode_hashid(id):
    """Кодирует идентификатор в короткую строку с помощью Hashids."""
    if id is None:
        return ''
    try:
        return _HASHIDS.encode(int(id))
    except (TypeError, ValueError):
        return ''


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
    return request.build_absolute_uri(f'/s/{encoded_id}/')


def get_id_from_short_link(code):
    """Получает идентификатор из короткой ссылки."""
    return decode_hashid(code)
