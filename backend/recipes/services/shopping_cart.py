from django.conf import settings
from django.db.models import F, Sum
from django.utils import timezone as tz

from recipes.models import Recipe, RecipeIngredient

SHOPPING_CART_FILENAME = getattr(
    settings, 'SHOPPING_CART_FILENAME', 'shopping_cart'
)


def get_shopping_cart_recipes(user):
    """Возвращает список рецептов пользователя из списка покупок"""
    return (
        Recipe.objects.filter(in_shoppingcarts__user=user)
        .values('name', author_name=F('author__username'))
        .distinct()
        .order_by('name')
    )


def get_shopping_cart_ingredients(user):
    """Возвращает список ингредиентов пользователя из списка покупок"""
    return (
        RecipeIngredient.objects.filter(recipe__in_shoppingcarts__user=user)
        .values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit'),
        )
        .annotate(total_amount=Sum('amount'))
        .order_by('name')
    )


def render_as_txt(data):
    """Форматирует список ингредиентов в текстовый файл"""
    header = f'Список покупок на {tz.localdate()}:'
    products_header = '№ - Наименование - Количество Единица измерения'
    recipes_header = 'Рецепты в вашем списке покупок:'
    products = [
        f'{num} - {item["name"].capitalize()} - '
        f'{item["total_amount"]} {item["measurement_unit"]}'
        for num, item in enumerate(data['ingredients'], start=1)
    ]
    recipes = [
        f'{recipe["name"].capitalize()} (автор: {recipe["author_name"]})'
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


def build_shopping_cart_file(*, user, file_format='txt'):
    """
    Возвращает (content, filename, content_type)
    или кидает ValidationError.
    """
    renderer = (render_as_txt, 'text/plain; charset=utf-8')
    data = {
        'ingredients': list(get_shopping_cart_ingredients(user)),
        'recipes': list(get_shopping_cart_recipes(user)),
    }
    render_fn, content_type = renderer

    content = render_fn(data)
    filename = f'{SHOPPING_CART_FILENAME}.{file_format}'
    return content, filename, content_type
