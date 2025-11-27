from django.contrib.auth.models import AbstractUser
from django.db import models

import recipes.constants as const


class User(AbstractUser):
    email = models.EmailField(
        'Почта',
        max_length=const.EMAIL_MAX_LENGTH,
        unique=True,
    )
    avatar = models.ImageField(
        upload_to='users/images/', null=True, blank=True, default=None
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        default_related_name = 'authors'


class MeasurementUnit(models.Model):
    name = models.CharField(max_length=64, unique=True, verbose_name='Название')

    class Meta:
        verbose_name = 'Единица измерения'
        verbose_name_plural = 'Единицы измерения'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=32, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название')
    measurement_unit = models.ForeignKey(
        MeasurementUnit,
        on_delete=models.CASCADE,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredients'
        unique_together = ('name', 'measurement_unit')


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор'
    )
    name = models.CharField(max_length=256, verbose_name='Название')
    text = models.TextField(verbose_name='Описание')
    tags = models.ManyToManyField(Tag)
    cooking_time = models.PositiveSmallIntegerField(
        default=1, verbose_name='Время приготовления'
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', verbose_name='Ингредиенты'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None,
        verbose_name='Изображение',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField()
    measurement_unit = models.ForeignKey(
        MeasurementUnit, on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('recipe', 'ingredient')
