import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes import validators
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Subscription,
    Tag,
)
from recipes.validators import username_validation

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для управления пользователями Администратором."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        return False
        user = self.context.get('request').user
        return user.is_authenticated and (user.followings.count() > 0)


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def validate_username(self, username):
        return username_validation(username)


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения списка тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения списка ингредиентов."""

    measurement_unit = serializers.ReadOnlyField(source='measurement_unit.name')

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit.__str__'
    )
    amount = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Сериализатор для добавления ингредиентов в рецепт."""

    # id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецепта в списке рецептов"""

    ingredients = RecipeIngredientReadSerializer(
        many=True, source='recipe_ingredients'
    )
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_is_favorited(self, obj):
        """Показывает что рецепт в Избранном."""
        user = self.context.get('request').user
        return (
            user.is_authenticated and obj.favorites.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Показывает что  рецепт в Списке Покупок."""
        user = self.context.get('request').user
        return (
            user.is_authenticated and obj.shoppings.filter(user=user).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""

    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()

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
        validators.list_is_not_empty(value, field_name='ингредиенты')
        validators.no_repeating_id_in_list(value, field_name='ингредиенты')

        for ingredient in value:
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиентов должно быть больше нуля.'
                )
        ingredient_ids = [ingredient['id'] for ingredient in value]
        existing_ids = set(
            Ingredient.objects.filter(id__in=ingredient_ids).values_list(
                'id', flat=True
            )
        )
        missing_ids = set(ingredient_ids) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                f'Ингредиента(ов) с id={", ".join(map(str, missing_ids))} не существует.'
            )
        return value

    def validate_tags(self, value):
        validators.list_is_not_empty(value, field_name='теги')
        # if not value:
        #     raise serializers.ValidationError(
        #         'Нужен хотя бы один тег для рецепта.'
        #     )
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    def create_ingredients(self, ingredients, recipe):
        recipe_ingredients = []
        for ingredient_data in ingredients:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data['amount'],
                    measurement_unit=ingredient.measurement_unit,
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags, clear=True)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        if not (ingredients and tags):
            field_name = 'Ингредиенты' if not ingredients else 'Теги'
            raise serializers.ValidationError(
                'Не указано обязательное поле "{}"'.format(field_name)
            )
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.tags.set(tags, clear=True)
        instance.recipe_ingredients.all().delete()
        self.create_ingredients(ingredients, instance)

        instance.save()
        return instance

    def to_representation(self, instance):
        # import RecipeReadSerializer
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeForCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения рецепта в Моих Подписках.
    при добавлении рецепта в Избранное
    и добавлении в Список Покупок
    """

    class Meta:
        model = Recipe
        ordering = '-pub_date'
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribtionSerializer(serializers.ModelSerializer):
    author = UserSerializer(
        read_only=True,
        # queryset=User.objects.all(),
    )
    recipes = RecipeForCartSerializer(
        read_only=True,
        many=True,
        # queryset=Recipe.objects.all()
    )

    class Meta:
        model = Subscription
        fields = ('author', 'recipes')


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя.',
            )
        ]
