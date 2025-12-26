import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from recipes.models import (
    Ingredient,
    MeasurementUnit,
    Recipe,
    RecipeIngredient,
    Tag,
)

User = get_user_model()


@pytest.fixture
@pytest.mark.django_db
def author(django_user_model):
    return User.objects.create_user(
        username='user2',
        email='user2@example.com',
        first_name='User',
        last_name='Two',
        password='pass',
    )


@pytest.fixture
@pytest.mark.django_db
def user(django_user_model):
    return User.objects.create_user(
        username='user1',
        email='user1@example.com',
        first_name='User',
        last_name='One',
        password='pass',
    )


@pytest.fixture
def author_client(author):
    client = APIClient()
    client.force_login(author)
    return client


@pytest.fixture
def anonym_client():
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def unit():
    return MeasurementUnit.objects.create(name='g')


@pytest.fixture
@pytest.mark.django_db
def ingredient_apple(unit):
    return Ingredient.objects.create(name='Apple', measurement_unit=unit)


@pytest.fixture
@pytest.mark.django_db
def ingredient_banana(unit):
    return Ingredient.objects.create(name='Banana', measurement_unit=unit)


def create_tags():
    tags = []
    for i in range(1, 4):
        tag = Tag.objects.create(name=f'Tag{i}', slug=f'tag{i}')
        tags.append(tag)
    return tags


@pytest.fixture
@pytest.mark.django_db
def recipe1(author, unit, ingredient_apple, ingredient_banana):
    recipe1 = Recipe.objects.create(
        author=author,
        name='Recipe 1',
        text='Text',
        cooking_time=1,
    )
    recipe1.tags.set(Tag.objects.filter(id__in=[1, 2]))

    RecipeIngredient.objects.create(
        recipe=recipe1,
        ingredient=ingredient_apple,
        amount=100,
        measurement_unit=unit,
    )
    RecipeIngredient.objects.create(
        recipe=recipe1,
        ingredient=ingredient_banana,
        amount=1,
        measurement_unit=unit,
    )
    return recipe1


@pytest.fixture
@pytest.mark.django_db
def recipe2(author, unit, ingredient_apple):
    recipe2 = Recipe.objects.create(
        author=author,
        name='Recipe 2',
        text='Text',
        cooking_time=1,
    )
    recipe2.tags.set(
        Tag.objects.filter(
            id__in=[
                3,
            ]
        )
    )

    RecipeIngredient.objects.create(
        recipe=recipe2,
        ingredient=ingredient_apple,
        amount=50,
        measurement_unit=unit,
    )
    return recipe2


@pytest.fixture
@pytest.mark.django_db
def other_recipe(author, unit, ingredient_banana):
    other_recipe = Recipe.objects.create(
        author=author,
        name='Recipe 3',
        text='Text',
        cooking_time=1,
    )
    other_recipe.tags.set(Tag.objects.filter(id__in=[3, 4]))
    RecipeIngredient.objects.create(
        recipe=other_recipe,
        ingredient=ingredient_banana,
        amount=999,
        measurement_unit=unit,
    )
    return other_recipe
