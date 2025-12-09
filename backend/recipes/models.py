from django.contrib.auth.models import AbstractUser
from django.db import models

import recipes.constants as const
from foodgram.settings import AVATAR_IMAGE_PATH, RECIPE_IMAGE_PATH
from recipes.validators import username_validation


class User(AbstractUser):
    username = models.CharField(
        'Логин',
        max_length=const.USERNAME_MAX_LENGTH,
        unique=True,
        validators=[username_validation],
    )
    email = models.EmailField(
        'Почта',
        max_length=const.EMAIL_MAX_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        'Имя',
        max_length=const.MAX_NAME_LENGTH,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=const.MAX_NAME_LENGTH,
        blank=False,
        null=False,
    )
    avatar = models.ImageField(
        upload_to=AVATAR_IMAGE_PATH, null=True, blank=True, default=None
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        default_related_name = 'authors'
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


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

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор'
    )
    name = models.CharField(max_length=256, verbose_name='Название')
    text = models.TextField(verbose_name='Описание')
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')
    cooking_time = models.PositiveSmallIntegerField(
        default=1, verbose_name='Время приготовления, мин'
    )
    image = models.ImageField(
        upload_to=RECIPE_IMAGE_PATH,
        blank=True,
        null=True,
        default=None,
        verbose_name='Изображение',
    )
    pub_date = models.DateField(
        auto_now_add=True, verbose_name='Дата публикации'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(verbose_name='Количество')
    measurement_unit = models.ForeignKey(
        MeasurementUnit, on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('recipe', 'ingredient')


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites'
    )

    class Meta:
        default_related_name = 'favorites'
        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shoppings'
    )


class Subscription(models.Model):
    """
    Подписка:
        оbject.followings - на кого подписан пользователь
        object.followers - кто подписан на пользователя
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followings',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
    )

    class Meta:
        unique_together = ('user', 'author')
