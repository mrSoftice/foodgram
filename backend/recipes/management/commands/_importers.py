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
    unique_fields = ()

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
        if (
            self.model is None
            or self.filename_stem is None
            or not self.unique_fields
        ):
            raise RuntimeError(
                'Неверные параметры: '
                'установите model, filename_stem, unique_fields'
            )

        data_dir = Path(options['data_dir'])
        frmt = 'json'
        file_path = data_dir / f'{self.filename_stem}.{frmt}'

        created = self._load(file_path)

        self.stdout.write(
            self.style.SUCCESS(
                f'Файл {file_path}.\n'
                rf'Всего в файле {self.model.objects.count()}.\т'
                f'Загружено {len(created)} элементов.'
            )
        )

    def _load(self, filename: Path):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        existing = set(self.model.objects.values_list(*self.unique_fields))

        to_create = []
        for row in data:
            key = tuple(row[field] for field in self.unique_fields)
            if key in existing:
                continue
            to_create.append(self.model(**row))
            existing.add(key)

        return self.model.objects.bulk_create(to_create)
