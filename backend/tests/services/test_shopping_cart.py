import pytest
from django.utils import timezone as tz

from foodgram.settings import SHOPPING_CART_FILENAME
from recipes.models import ShoppingCart
from recipes.services.shopping_cart import (
    build_shopping_cart_file,
    get_shopping_cart_ingredients,
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
            'measurement_unit': 'g',
            'total_amount': 150,
        },
        {
            'name': 'Banana',
            'measurement_unit': 'g',
            'total_amount': 1,
        },
    ]


def test_render_as_txt(recipe1, recipe2):
    header = f'Список покупок на {tz.localdate()}:'
    products_header = '№ - Наименование - Количество Единица измерения'
    recipes_header = 'Рецепты в вашем списке покупок:'

    data = {
        'ingredients': [
            {'name': 'Sugar', 'total_amount': 10, 'measurement_unit': 'g'},
            {'name': 'Salt', 'total_amount': 1, 'measurement_unit': 'g'},
        ],
        'recipes': [
            {'name': 'Recipe 1', 'author_name': 'User2'},
            {'name': 'Recipe 2', 'author_name': 'User2'},
        ],
    }
    expected = '\n'.join(
        [
            header,
            products_header,
            '1 - Sugar - 10 g',
            '2 - Salt - 1 g',
            '',
            recipes_header,
            'Recipe 1 (автор: User2)',
            'Recipe 2 (автор: User2)',
        ]
    )
    assert render_as_txt(data) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    'file_format, expected_content_type',
    [
        ('txt', 'text/plain; charset=utf-8'),
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
    header = f'Список покупок на {tz.localdate()}:'
    products_header = '№ - Наименование - Количество Единица измерения'
    recipes_header = 'Рецепты в вашем списке покупок:'

    if file_format == 'txt':
        assert content.splitlines() == [
            header,
            products_header,
            '1 - Apple - 150 g',
            '2 - Banana - 1 g',
            '',
            recipes_header,
            'Recipe 1 (автор: user2)',
            'Recipe 2 (автор: user2)',
        ]


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
