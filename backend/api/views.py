from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Exists, OuterRef, Prefetch, Value
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api import filters, pagination, serializers
from api.permissions import IsAuthorOrReadOnly
from foodgram.settings import (
    SHOPPING_CART_FILENAME,
    SHOPPING_CART_FORMAT,
    USER_SELFINFO_PATH,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
)
from recipes.services.shopping_cart import (
    build_file_response,
    get_shopping_cart_ingredients,
    render_as_csv,
    render_as_json,
    render_as_txt,
)
from recipes.services.short_links import get_short_link

User = get_user_model()


class UserViewSet(ModelViewSet):
    lookup_field = 'id'
    permission_classes = (AllowAny,)
    pagination_class = pagination.PageLimitPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return (AllowAny(),)
        return (IsAuthenticated(),)

    def get_queryset(self):
        queryset = User.objects.all()

        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_subscribed=Exists(
                    Subscription.objects.filter(
                        user=user, author=OuterRef('pk')
                    )
                )
            )
        else:
            queryset = queryset.annotate(
                is_subscribed=Value(False, output_field=BooleanField())
            )
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.UserCreateSerializer
        return serializers.UserSerializer

    @action(methods=['GET'], detail=False, url_path=USER_SELFINFO_PATH)
    def me(self, request):
        serializer = serializers.UserSerializer(
            self.get_queryset().get(pk=request.user.pk),
            context={'request': request},
        )
        return Response(serializer.data)

    @action(
        methods=['POST'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        serializer = serializers.SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(
            serializer.validated_data['current_password']
        ):
            return Response(
                {'current_password': ['Неверный текущий пароль.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(
            {'status': 'Пароль изменен'}, status=status.HTTP_204_NO_CONTENT
        )

    @action(
        methods=['PUT', 'DELETE'],
        detail=False,
        url_path=USER_SELFINFO_PATH + '/avatar',
        url_name='avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = serializers.UserAvatarSerializer(
                user, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        page = self.paginate_queryset(
            User.objects.filter(followers__user=request.user)
        )
        serializer = serializers.SubscribtionReadSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'PUT'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)

        create_subscription = serializers.SubscribtionWriteSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request},
        )
        create_subscription.is_valid(raise_exception=True)
        create_subscription.save()

        read_subscription = serializers.SubscribtionReadSerializer(
            author, context={'request': request}
        )

        return Response(read_subscription.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        user = request.user
        try:
            subscription = user.subscriptions.get(author=author)
        except Subscription.DoesNotExist:
            return Response(
                {'errors': 'Вы не подписаны на данного пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None
    filterset_fields = ('name',)


class IngredientsViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filterset_class = filters.IngredientFilter


class RecipesViewSet(ModelViewSet):
    pagination_class = pagination.PageLimitPagination
    filterset_class = filters.RecipeFilters
    permission_classes = (IsAuthorOrReadOnly,)

    @action(methods=['GET'], detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        short_link = get_short_link(recipe.id, request)

        return Response({'short-link': short_link})

    @action(methods=['POST', 'DELETE'], detail=True, url_path='favorite')
    def favorite(self, request, pk=None):
        return self._manage_recipe_relation(
            request, pk, serializers.FavoriteSerializer, Favorite
        )

    @action(methods=['POST', 'DELETE'], detail=True, url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        return self._manage_recipe_relation(
            request, pk, serializers.ShoppingCartSerializer, ShoppingCart
        )

    @action(methods=['GET'], detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        file_format = request.query_params.get('file_format', None)
        if file_format is None:
            file_format = SHOPPING_CART_FORMAT
        data = get_shopping_cart_ingredients(request.user)
        filename = f'{SHOPPING_CART_FILENAME}.{file_format}'
        if file_format == 'csv':
            file_content = render_as_csv(data)
            content_type = 'text/csv'
        elif file_format == 'json':
            file_content = render_as_json(data)
            content_type = 'aplication/json'
        else:
            file_content = render_as_txt(data)
            content_type = 'text/plain'
        return build_file_response(file_content, filename, content_type)

    def _manage_recipe_relation(self, request, pk, serializer_class, model):
        if request.user.is_anonymous:
            return Response(
                {'errors': 'Авторизуйтесь для выполнения данного действия.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            write_serializer = serializer_class(
                data={'user': request.user.id, 'recipe': recipe.id},
                context={'request': request},
            )
            write_serializer.is_valid(raise_exception=True)
            write_serializer.save()

            read_serializer = serializers.RecipeForCartSerializer(
                recipe, context={'request': request}
            )
            return Response(
                read_serializer.data, status=status.HTTP_201_CREATED
            )
        else:
            try:
                relation_instance = model.objects.filter(
                    user=request.user, recipe=recipe
                ).get()
            except model.DoesNotExist:
                return Response(
                    {'errors': 'Рецепт не найден в списке.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            relation_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        user = self.request.user

        author_queryset = User.objects.all()
        if user.is_authenticated:
            annotation = Exists(
                Subscription.objects.filter(user=user, author=OuterRef('pk'))
            )
        else:
            annotation = Value(False, output_field=BooleanField())
        author_queryset = author_queryset.annotate(is_subscribed=annotation)

        base_queryset = Recipe.objects.all().prefetch_related(
            Prefetch('author', queryset=author_queryset),
            'tags',
            'recipe_ingredients__ingredient__measurement_unit',
            'recipe_ingredients__measurement_unit',
        )
        if user.is_authenticated:
            return base_queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                ),
            )
        return base_queryset

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeReadSerializer
        return serializers.RecipeCreateSerializer
