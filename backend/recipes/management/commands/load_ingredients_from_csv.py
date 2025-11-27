import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from foodgram import settings
from recipes.models import Ingredient, MeasurementUnit


class Command(BaseCommand):
    """
    Команда для загрузки ингредиентов из CSV-файла.
    Проверка уникальности вручную по комбинации (name, measurement_unit), чтобы избежать ошибок ON CONFLICT в SQLite.
    bulk_create только для новых объектов, дубликаты пропускаются.
    Работает как с уже существующими MeasurementUnit, так и с новыми.
    """

    help = 'Load ingredients list from CSV file'

    def handle(self, *args, **options):
        # Загрузка категорий
        data_path = Path(settings.BASE_DIR).parent / 'data'
        full_file_name = data_path / 'ingredients.csv'
        with open(full_file_name, 'r', encoding='utf-8') as f:
            rows_from_file = list(csv.DictReader(f))

        unit_names = {row['measurement_unit'] for row in rows_from_file}

        existing_units = MeasurementUnit.objects.filter(name__in=unit_names)
        existing_unit_names = set(unit.name for unit in existing_units)

        m_units_to_create = [
            MeasurementUnit(name=name)
            for name in unit_names
            if name not in existing_unit_names
        ]
        print(m_units_to_create)
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
                for row in rows_from_file
                if (row['name'], row['measurement_unit'])
                not in existing_ingredients
            ]
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded {len(created_ingredients)} ingredients'
            )
        )
