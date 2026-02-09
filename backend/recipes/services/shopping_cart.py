from django.db.models import F, Sum
from django.utils import timezone as tz
from django.utils.formats import date_format

from recipes.models import Recipe, RecipeIngredient

SHOPPING_CART_FILENAME = 'shopping_cart'
SHOPPING_CART_FORMAT = 'txt'


def get_shopping_cart_recipes(user):
    """Возвращает список рецептов пользователя из списка покупок"""
    return (
        Recipe.objects.filter(shoppingcarts__user=user)
        .distinct()
        .order_by('name')
    )


def get_shopping_cart_ingredients(user):
    """Возвращает список ингредиентов пользователя из списка покупок"""
    return (
        RecipeIngredient.objects.filter(recipe__shoppingcarts__user=user)
        .values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit'),
        )
        .annotate(total_amount=Sum('amount'))
        .order_by('name')
    )


def render_as_txt(data):
    """Форматирует список ингредиентов в текстовый файл"""
    header = (
        f'Список покупок на {date_format(tz.localdate(), format="d E Y")}:'
    )
    products_header = '№ - Наименование - Единица измерения - Количество'
    recipes_header = 'Рецепты в вашем списке покупок:'
    products = [
        f'{num} - {item["name"].capitalize()} - ({item["measurement_unit"]})'
        f' - {item["total_amount"]}'
        for num, item in enumerate(data['ingredients'], start=1)
    ]
    recipes = [
        f'{recipe.name.capitalize()} (автор: {recipe.author.username})'
        for recipe in data['recipes']
    ]

    return '\n'.join(
        [
            header,
            products_header,
            *products,
            '',
            recipes_header,
            *recipes,
        ]
    )
