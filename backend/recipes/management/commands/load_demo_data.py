from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from recipes.management.commands.load_ingredients import (
    load_ingredients,
    load_units,
)
from recipes.models import (
    Ingredient,
    MeasurementUnit,
    Recipe,
    RecipeIngredient,
    Tag,
)
from recipes.services.utils import read_data_from_file

User = get_user_model()


class Command(BaseCommand):
    help = 'Загрузка демо-данных из JSON: '
    'tags.json, ingredients.json, users.json, recipes.json.\n'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default='../data',
            help='Каталог с JSON файлами (по умолчанию /data).',
        )

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])

        tags_path = data_dir / 'tags.json'
        units_path = data_dir / 'units.json'
        ingredients_path = data_dir / 'ingredients.json'
        users_path = data_dir / 'users.json'
        recipes_path = data_dir / 'recipes.json'

        for p in (tags_path, ingredients_path, users_path, recipes_path):
            if not p.exists():
                raise CommandError(
                    f'Не найден файл: {p}. '
                    f'Проверьте volume-mount и размещение данных в {data_dir}.'
                )

        with transaction.atomic():
            self._load_users(users_path)
            self._load_tags(tags_path)
            self._load_units(units_path)
            self._load_ingredients(ingredients_path)
            self._load_recipes(recipes_path)

        self.stdout.write(self.style.SUCCESS('Демо-данные успешно загружены.'))

    def _load_tags(self, path):
        data = read_data_from_file(path)

        created = 0
        for item in data:
            _, was_created = Tag.objects.get_or_create(
                slug=item['slug'],
                defaults={'name': item['name']},
            )
            created += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f'Теги: создано {created}, всего {Tag.objects.count()}.'
            )
        )

    def _load_units(self, path):
        created = load_units(path)

        self.stdout.write(
            self.style.SUCCESS(
                f'Единицы измерения: создано {len(created)}, '
                f'всего {MeasurementUnit.objects.count()}.'
            )
        )

    def _load_users(self, path):
        data = read_data_from_file(path)

        created = 0
        for item in data:
            user, was_created = User.objects.get_or_create(
                email=item['email'],
                defaults={
                    'username': item['username'],
                    'first_name': item['first_name'],
                    'last_name': item['last_name'],
                },
            )
            if was_created:
                user.set_password(item['password'])
                user.save()
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Пользователи: создано {created}, всего {User.objects.count()}'
            )
        )

    def _load_recipes(self, path: Path) -> None:
        data = read_data_from_file(path)

        created_recipes = 0
        created_links = 0

        for item in data:
            author = User.objects.get(email=item['author_email'])

            recipe, was_created = Recipe.objects.get_or_create(
                author=author,
                name=item['name'],
                defaults={
                    'text': item['text'],
                    'cooking_time': item['cooking_time'],
                },
            )

            if not was_created:
                # Рецепт уже был — не плодим дубликаты связей
                continue

            created_recipes += 1

            # Теги (slug)
            tags = Tag.objects.filter(slug__in=item['tags'])
            if tags.count() != len(item['tags']):
                missing = set(item['tags']) - set(
                    tags.values_list('slug', flat=True)
                )
                raise CommandError(
                    f'Не найдены теги по slug: {sorted(missing)}'
                )
            recipe.tags.add(*tags)

            # Ингредиенты (name + measurement_unit)
            for ing in item['ingredients']:
                unit = MeasurementUnit.objects.get(name=ing['measurement_unit'])
                ingredient = Ingredient.objects.get(
                    name=ing['name'], measurement_unit=unit
                )

                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ing['amount'],
                    measurement_unit=unit,
                )
                created_links += 1

        self.stdout.write(
            self.style.SUCCESS(f'Рецепты: создано {created_recipes}.')
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Связи RecipeIngredient: создано {created_links}.'
            )
        )

    def _load_ingredients(self, path):
        created = load_ingredients(path)

        self.stdout.write(
            self.style.SUCCESS(
                f'Ингредиенты: создано {len(created)}, '
                f'всего {Ingredient.objects.count()}'
            )
        )
