import json
from pathlib import Path

from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    """
    Базовая команда импорта.
    Наследники задают только поля класса:
    - model
    - filename_stem (например 'ingredients' или 'tags')
    - unique_fields (кортеж полей уникальности)
    - build_instance(row) -> объект модели
    """

    model = None
    filename_stem = None

    help = (
        'Импортирует данные из файла json. '
        'Параметры:  --data-dir (default: ./data)'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default='./data',
            help='Каталог с файлами данных (по умолчанию ./data).',
        )

    def handle(self, *args, **options):
        try:
            data_dir = Path(options['data_dir'])
            file_path = data_dir / f'{self.filename_stem}.json'

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            created = self.model.objects.bulk_create(
                [tuple(row[field] for field in row) for row in data],
                ignore_conflicts=True,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Файл {file_path}.\n'
                    rf'Всего в файле {self.model.objects.count()}.\т'
                    f'Загружено {len(created)} элементов.'
                )
            )
        except Exception:
            raise RuntimeError(
                'Неверные параметры: '
                'установите model, filename_stem, unique_fields'
            )
