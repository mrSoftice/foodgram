from django.db.models import F, Sum
from django.http import HttpResponse

from recipes.models import RecipeIngredient


def get_shopping_cart_ingredients(user):
    """Возвращает список ингредиентов пользователя из списка покупок"""
    return (
        RecipeIngredient.objects.filter(recipe__shoppingcart__user=user)
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


def build_file_response(file_content, filename, content_type):
    """Создает HTTP ответ с файлом для скачивания"""

    response = HttpResponse(file_content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
