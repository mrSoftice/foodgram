import json
from pathlib import Path

from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    """
    Базовая команда импорта.
    Наследники задают только поля класса:
    - model
    """

    model = None
    help = (
        'Импортирует данные из файла json. '
        'Параметры:  --data-file (default: ./data/ingredients.json)'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-file',
            default='./data/ingredients.json',
            help='Каталог с файлами данных (по умолчанию ./data).',
        )

    def handle(self, *args, **options):
        try:
            file_path = Path(options['data_file'])

            with open(file_path, 'r', encoding='utf-8') as f:
                created = self.model.objects.bulk_create(
                    (self.model(*row) for row in json.load(f)),
                    ignore_conflicts=True,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Файл {file_path}.\n'
                    rf'Всего в файле {self.model.objects.count()}.\n'
                    f'Загружено {len(created)} элементов.'
                )
            )
        except Exception as e:
            raise RuntimeError(
                f'Ошибка загрузки "{self.model._meta.verbose_name_plural}":\n'
                f'Причина: {e}'
            ) from e
