from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Tag
from recipes.services.utils import read_data_from_file


class Command(BaseCommand):
    """
    Команда для загрузки Тегов из json-файла.
    Проверка уникальности вручную по комбинации (name, slug),'
    чтобы избежать ошибок ON CONFLICT в SQLite.
    bulk_create только для новых объектов, дубликаты пропускаются.
    """

    help = (
        'Load Tags list from file. '
        'Parameters: '
        '  --data-dir (default: ./data) '
        '  --format (csv or json, default: json)'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default='./data',
            help='Каталог с JSON файлами (по умолчанию ./data).',
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

        file_path = Path(data_dir, 'tags.' + frmt)

        created_tags = load_tags(file_path)
        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено {len(created_tags)} тегов, '
                f'всего {Tag.objects.count()}.'
            )
        )


def load_tags(filename):
    data = read_data_from_file(filename)
    existing_elements = set(Tag.objects.values_list('name', 'slug'))

    created_elements = Tag.objects.bulk_create(
        [
            Tag(
                name=row['name'],
                measurement_unit=row['slug'],
            )
            for row in data
            if (row['name'], row['slug']) not in existing_elements
        ]
    )
    return created_elements
