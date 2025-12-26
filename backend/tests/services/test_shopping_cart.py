import json

import pytest

from recipes.models import ShoppingCart
from recipes.services.shopping_cart import (
    build_file_response,
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
    expected = (
        'Ingredient - Total Amount - Measurement Unit\nSugar - 10 g\nSalt - 1 g'
    )
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


def test_build_file_response():
    response = build_file_response('abc', 'file.txt', 'text/plain')

    assert response.content == b'abc'
    assert response['Content-Disposition'] == 'attachment; filename="file.txt"'
    assert response['Content-Type'].startswith('text/plain')
