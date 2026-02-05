from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes import validators
from recipes.constants import INGREDIENT_MIN_AMOUNT
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для управления пользователями Администратором."""

    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar',
        )
        read_only_fields = fields


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения списка тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения списка ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')
        read_only_fields = fields


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Сериализатор для добавления ингредиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=INGREDIENT_MIN_AMOUNT)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецепта в списке рецептов"""

    ingredients = RecipeIngredientReadSerializer(
        many=True, source='ingredients_amounts'
    )
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""

    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Поле "Ингредиенты" не должно быть пустым.'
            )
        validators.no_repeating_elements_in_list(
            value, list_name='ингредиенты'
        )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Поле "Теги" не должно быть пустым.'
            )
        validators.no_repeating_elements_in_list(value, list_name='теги')
        return value

    def create_ingredients(self, ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'],
            )
            for ingredient_data in ingredients
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = super().create(validated_data)
        recipe.tags.set(tags, clear=True)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            instance.ingredients_amounts.all().delete()
            self.create_ingredients(ingredients, instance)

        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            self.context.get('view').get_queryset().get(pk=instance.pk),
            context=self.context,
        ).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения рецепта в Моих Подписках.
    при добавлении рецепта в Избранное
    и добавлении в Список Покупок
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class FollowedAuthorWithRecipesSerializer(UserSerializer):
    """
    Возвращает информацию об авторах и их рецептах
    на которых подписан текущий пользователь.
    """

    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            *UserSerializer.Meta.fields,
            'recipes_count',
            'recipes',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()

        recipes_limit = request.GET.get('recipes_limit')
        if recipes_limit is None:
            return RecipeShortSerializer(recipes, many=True).data
        try:
            limit = int(recipes_limit)
        except (TypeError, ValueError):
            raise serializers.ValidationError(
                {'recipes_limit': 'recipes_limit должен быть целым числом.'}
            )

        recipes = recipes[:limit]
        return RecipeShortSerializer(recipes, many=True).data
