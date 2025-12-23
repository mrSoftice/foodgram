from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient, MeasurementUnit
from recipes.services.utils import read_data_from_file


class Command(BaseCommand):
    """
    Команда для загрузки ингредиентов из CSV-файла.
    Проверка уникальности вручную по комбинации (name, measurement_unit), чтобы избежать ошибок ON CONFLICT в SQLite.
    bulk_create только для новых объектов, дубликаты пропускаются.
    Работает как с уже существующими MeasurementUnit, так и с новыми.
    """

    help = (
        'Load ingredients list from file. '
        'Parameters: --data-dir (default: ../data) --format (csv or json, default: json)'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default='../data',
            help='Каталог с JSON файлами (по умолчанию /data).',
        )
        parser.add_argument(
            '--format',
            default='json',
            choices=['csv', 'json'],
            help='Формат файла с ингредиентами (по умолчанию json).',
        )

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])
        frmt = options['format']

        units_path = Path(data_dir, 'units.' + frmt)
        ingredients_path = Path(data_dir, 'ingredients.' + frmt)

        for p in (units_path, ingredients_path):
            if not p.exists():
                raise CommandError(
                    f'Не найден файл: {p}. '
                    f'Проверьте volume-mount и размещение данных в {data_dir}.'
                )

        created_units = load_units(units_path)
        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено {len(created_units)} единиц измерения, всего {MeasurementUnit.objects.count()}.'
            )
        )

        created_ingredients = load_ingredients(ingredients_path)
        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено {len(created_ingredients)} ингредиентов, всего {Ingredient.objects.count()}.'
            )
        )


def load_units(filename):
    # Загрузка единиц измерения из JSON-файла
    data = read_data_from_file(filename)

    created = 0
    created_items = []
    for item in data:
        mu, was_created = MeasurementUnit.objects.get_or_create(
            name=item['name'],
        )

        if was_created:
            created += int(was_created)
            created_items.append(mu)

    return created_items


def load_ingredients(filename):
    data = read_data_from_file(filename)
    unit_names = {row['measurement_unit'] for row in data}

    existing_units = MeasurementUnit.objects.filter(name__in=unit_names)
    existing_unit_names = set(unit.name for unit in existing_units)

    m_units_to_create = [
        MeasurementUnit(name=name)
        for name in unit_names
        if name not in existing_unit_names
    ]

    MeasurementUnit.objects.bulk_create(
        m_units_to_create,
        update_conflicts=True,
        update_fields=['name'],
        unique_fields=['name'],
    )

    # Обновляем маппинг
    units_map = {
        unit.name: unit
        for unit in MeasurementUnit.objects.filter(name__in=unit_names)
    }
    existing_ingredients = set(
        Ingredient.objects.values_list('name', 'measurement_unit__name')
    )

    created_ingredients = Ingredient.objects.bulk_create(
        [
            Ingredient(
                name=row['name'],
                measurement_unit=units_map[row['measurement_unit']],
            )
            for row in data
            if (row['name'], row['measurement_unit'])
            not in existing_ingredients
        ]
    )
    return created_ingredients
