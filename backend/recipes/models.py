from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

import recipes.constants as const

AVATAR_IMAGE_PATH = getattr(settings, 'AVATAR_IMAGE_PATH', '')
RECIPE_IMAGE_PATH = getattr(settings, 'RECIPE_IMAGE_PATH', '')
USERNAME_PATTERN = getattr(settings, 'USERNAME_PATTERN', r'^[\w.@+-]+\z')


class User(AbstractUser):
    username = models.CharField(
        'Логин',
        max_length=const.USERNAME_MAX_LENGTH,
        unique=True,
        validators=[RegexValidator(USERNAME_PATTERN)],
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
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Tag(models.Model):
    name = models.CharField(
        max_length=32, unique=True, verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=32, unique=True, verbose_name='Идентификатор'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=64, verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit_in_Ingredient',
            )
        ]
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор'
    )
    name = models.CharField(max_length=256, verbose_name='Название')
    text = models.TextField(verbose_name='Описание')
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги', related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления, мин',
        validators=(MinValueValidator(1),),
    )
    image = models.ImageField(
        upload_to=RECIPE_IMAGE_PATH,
        verbose_name='Изображение',
    )
    pub_date = models.DateField(
        auto_now_add=True, verbose_name='Дата публикации'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredients_amounts'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='in_recipes'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество', validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe',
            )
        ]


class UserRecipeRelation(models.Model):
    """Связь user <-> recipe (избранное/корзина и т.п.)."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='%(class)s_items'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='in_%(class)ss'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_%(class)s_user_per_recipe',
            )
        ]

    def __str__(self):
        return f'{self.recipe.name} (для {self.user.username})'


class Favorite(UserRecipeRelation):
    class Meta:
        verbose_name = 'Избранное'
        default_related_name = 'favorites'


class ShoppingCart(UserRecipeRelation):
    class Meta:
        verbose_name = 'Список покупок'
        default_related_name = 'shoppingcarts'


class Subscription(models.Model):
    """
    Подписка:
        оbject.subscriptions - на кого подписан пользовpython manageатель
        object.authors - кто подписан на пользователя
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        # В новых версиях Django в конструкторе CheckConstraint
        # нужно использовать параметр condition вместо check
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription',
            ),
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription_per_user_per_author',
            ),
        ]
