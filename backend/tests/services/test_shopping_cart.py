import json

import pytest
from rest_framework.exceptions import ValidationError

from foodgram.settings import SHOPPING_CART_FILENAME
from recipes.models import ShoppingCart
from recipes.services import core
from recipes.services.shopping_cart import (
    build_shopping_cart_file,
    get_shopping_cart_ingredients,
    render_as_csv,
    render_as_json,
    render_as_txt,
)


@pytest.mark.django_db
def test_get_shopping_cart_ingredients_aggregates_and_sorts(
    recipe1,
    recipe2,
    other_recipe,
    author,
    user,
):
    ShoppingCart.objects.create(user=author, recipe=recipe1)
    ShoppingCart.objects.create(user=author, recipe=recipe2)
    ShoppingCart.objects.create(user=user, recipe=other_recipe)

    results = list(get_shopping_cart_ingredients(author))

    assert results == [
        {
            'name': 'Apple',
            'measure_unit': 'g',
            'total_amount': 150,
        },
        {
            'name': 'Banana',
            'measure_unit': 'g',
            'total_amount': 1,
        },
    ]


def test_render_as_txt():
    data = [
        {'name': 'Sugar', 'total_amount': 10, 'measure_unit': 'g'},
        {'name': 'Salt', 'total_amount': 1, 'measure_unit': 'g'},
    ]
    expected = 'Ingredient - Total Amount - Measurement Unit'
    '\nSugar - 10 g\nSalt - 1 g'
    assert render_as_txt(data) == expected


def test_render_as_csv():
    data = [
        {'name': 'Sugar', 'total_amount': 10, 'measure_unit': 'g'},
    ]
    result = render_as_csv(data).splitlines()
    assert result[0] == 'Ingredient,Total Amount,Measurement Unit'
    assert result[1] == 'Sugar,10,g'


def test_render_as_json():
    data = [
        {'name': 'Sugar', 'total_amount': 10, 'measure_unit': 'g'},
    ]
    payload = render_as_json(data)
    assert json.loads(payload) == [
        {'name': 'Sugar', 'amount': 10, 'measurement_unit': 'g'}
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'file_format, expected_content_type',
    [
        ('txt', 'text/plain; charset=utf-8'),
        ('csv', 'text/csv; charset=utf-8'),
        ('json', 'application/json; charset=utf-8'),
    ],
)
def test_build_shopping_cart_file_returns_content_filename_and_type(
    file_format,
    expected_content_type,
    recipe1,
    recipe2,
    author,
):
    # author добавляет 2 рецепта в shopping cart
    ShoppingCart.objects.create(user=author, recipe=recipe1)
    ShoppingCart.objects.create(user=author, recipe=recipe2)

    content, filename, content_type = build_shopping_cart_file(
        user=author,
        file_format=file_format,
    )
    assert filename == f'{SHOPPING_CART_FILENAME}.{file_format}'
    assert content_type == expected_content_type

    # Содержимое проверяем по формату
    if file_format == 'txt':
        assert content.splitlines() == [
            'Ingredient - Total Amount - Measurement Unit',
            'Apple - 150 g',
            'Banana - 1 g',
        ]
    elif file_format == 'csv':
        lines = content.splitlines()
        assert lines[0] == 'Ingredient,Total Amount,Measurement Unit'
        assert lines[1] == 'Apple,150,g'
        assert lines[2] == 'Banana,1,g'

    elif file_format == 'json':
        assert json.loads(content) == [
            {'name': 'Apple', 'amount': 150, 'measurement_unit': 'g'},
            {'name': 'Banana', 'amount': 1, 'measurement_unit': 'g'},
        ]


@pytest.mark.django_db
def test_build_shopping_cart_file_raises_validation_error_on_empty_cart(
    author,
):
    # У author нет позиций в shopping cart
    with pytest.raises(ValidationError) as exc_info:
        build_shopping_cart_file(user=author, file_format='txt')

    # Не привязываемся к структуре detail (может быть list/dict/ErrorDetail),
    # но убеждаемся, что текст "пустой список" присутствует.
    assert core.ERROR_EMPTY['errors'] in str(exc_info.value.detail)


@pytest.mark.django_db
def test_add_to_shopping_cart_authenticated_user_ok(
    user_client,
    user,
    recipe1,
    shopping_cart_url,
):
    response = user_client.post(shopping_cart_url, data={}, format='json')

    assert response.status_code == 201
    assert ShoppingCart.objects.filter(user=user, recipe=recipe1).exists()


@pytest.mark.django_db
def test_add_to_shopping_cart_anonymous_user_unauthorized(
    anonym_client,
    recipe1,
    shopping_cart_url,
):
    initial_count = ShoppingCart.objects.count()

    response = anonym_client.post(shopping_cart_url, data={}, format='json')

    assert response.status_code == 401
    assert ShoppingCart.objects.count() == initial_count
