import pytest

from recipes.services import short_links


def test_encode_decode_base62_roundtrip():
    nums = [0, 1, 10, 61, 62, 1000, 99999]
    for num in nums:
        encoded = short_links.encode_base62(num)
        assert short_links.decode_base62(encoded) == num


def test_encode_base62_zero_uses_first_alphabet_char():
    assert short_links.encode_base62(0) == short_links.BASE62_ALPHABET[0]


def test_encode_decode_hashid_roundtrip():
    ids = [1, 7, 123, 9999]
    for value in ids:
        encoded = short_links.encode_hashid(value)
        assert short_links.decode_hashid(encoded) == value


def test_decode_hashid_invalid_raises_value_error():
    with pytest.raises(ValueError):
        short_links.decode_hashid('not-a-valid-code')


def test_get_short_link_uses_request_builder():
    class DummyRequest:
        def __init__(self):
            self.paths = []

        def build_absolute_uri(self, path):
            self.paths.append(path)
            return f'http://testserver{path}'

    request = DummyRequest()
    encoded = short_links.encode_hashid(42)

    url = short_links.get_short_link(42, request)

    assert url == f'http://testserver/s/{encoded}'
    assert request.paths == [f'/s/{encoded}']


def test_get_id_from_short_link_decodes_hashid():
    code = short_links.encode_hashid(5)
    assert short_links.get_id_from_short_link(code) == 5
