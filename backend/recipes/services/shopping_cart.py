from django.conf import settings
from django.db.models import F, Sum
from rest_framework.exceptions import ValidationError

from recipes.models import RecipeIngredient
from recipes.services import core

SHOPPING_CART_FORMAT = getattr(
    settings, 'SHOPPING_CART_FILENAME', 'shopping_cart'
)


def get_shopping_cart_ingredients(user):
    """Возвращает список ингредиентов пользователя из списка покупок"""
    return (
        RecipeIngredient.objects.filter(recipe__in_shoppingcarts__user=user)
        .values(
            name=F('ingredient__name'),
            measure_unit=F('measurement_unit__name'),
        )
        .annotate(total_amount=Sum('amount'))
        .order_by('name')
    )


def render_as_txt(data):
    """Форматирует список ингредиентов в текстовый файл"""
    lines = ['Ingredient - Total Amount - Measurement Unit']
    lines += [
        f'{item["name"]} - {item["total_amount"]} {item["measure_unit"]}'
        for item in data
    ]
    return '\n'.join(lines)


def render_as_csv(data):
    """Форматирует список ингредиентов в CSV файл"""
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ingredient', 'Total Amount', 'Measurement Unit'])
    for item in data:
        writer.writerow(
            [
                item['name'],
                item['total_amount'],
                item['measure_unit'],
            ]
        )
    return output.getvalue()


def render_as_json(data):
    """Форматирует список ингредиентов в JSON файл"""
    import json

    result = [
        {
            'name': item['name'],
            'amount': item['total_amount'],
            'measurement_unit': item['measure_unit'],
        }
        for item in data
    ]
    return json.dumps(result, ensure_ascii=False, indent=2)


_RENDERERS = {
    'txt': (render_as_txt, 'text/plain; charset=utf-8'),
    'csv': (render_as_csv, 'text/csv; charset=utf-8'),
    'json': (render_as_json, 'application/json; charset=utf-8'),
}


def build_shopping_cart_file(*, user, file_format):
    """
    Возвращает (content, filename, content_type)
    или кидает ValidationError.
    """
    renderer = _RENDERERS.get(file_format)
    data = list(get_shopping_cart_ingredients(user))

    if not data:
        raise ValidationError(core.ERROR_EMPTY)

    render_fn, content_type = renderer

    content = render_fn(data)
    filename = f'{SHOPPING_CART_FILENAME}.{file_format}'
    return content, filename, content_type
