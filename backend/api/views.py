from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import (
    NotAuthenticated,
    NotFound,
    ValidationError,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api import filters, pagination, serializers
from api.permissions import IsAuthorOrReadOnly
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
)
from recipes.services import core, subscriptions
from recipes.services.shopping_cart import build_shopping_cart_file

User = get_user_model()

SHOPPING_CART_FORMAT = getattr(settings, 'SHOPPING_CART_FORMAT', 'txt')


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    lookup_field = 'id'
    permission_classes = (AllowAny,)
    pagination_class = pagination.PageLimitPagination

    def get_queryset(self):
        return subscriptions.annotate_is_subscribed(
            super().get_queryset(), self.request.user
        )

    @action(
        methods=['GET'],
        detail=False,
        url_path='me',
        permission_classes=[IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        methods=['PUT', 'DELETE'],
        detail=False,
        url_path='me/avatar',
        url_name='avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        user = request.user
        if request.method != 'PUT':
            if user.avatar:
                user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = serializers.UserAvatarSerializer(
            user, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        return self.get_paginated_response(
            serializers.SubscribedAuthorSerializer(
                self.paginate_queryset(
                    User.objects.filter(authors__user=request.user)
                ),
                many=True,
                context={'request': request},
            ).data
        )

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)

        try:
            self._subscribe(request.user, author)
        except (ValidationError, NotAuthenticated) as e:
            return Response(e.detail, status=e.status_code)

        return Response(
            serializers.SubscribedAuthorSerializer(
                author, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        # author = subscriptions.get_author_or_404(id)
        self._unsubscribe(request.user, id)
        return core.SUCCESS_DELETED_RESPONSE

    def _subscribe(self, user, author):
        """
        Создает подписку на автора.
        Возвращает:
        - Subscription (успех)
        - Поднимает исключение ValidationError (ошибка)
        """
        _, created = Subscription.objects.get_or_create(
            user=user,
            author=author,
        )
        if not created:
            raise ValidationError(
                core.format_error(
                    core.ERROR_ALREADY_SUBSCRIBED, author=author.username
                )
            )

    def _unsubscribe(self, user, author_id):
        """Удаляет подписку на автора.
        Возвращает:
        - None (успех)
        - Response (ошибка)
        """

        get_object_or_404(
            Subscription, user=user, author__id=author_id
        ).delete()


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
        if not Recipe.objects.filter(pk=pk).exists():
            raise NotFound('Recipe not found.')
        return Response(
            {'short-link': request.build_absolute_uri(f'/s/{pk}/')}
        )

    @action(methods=['POST', 'DELETE'], detail=True, url_path='favorite')
    def favorite(self, request, pk=None):
        return self._manage_recipe_relation(
            request, pk, serializers.RecipeShortSerializer, Favorite
        )

    @action(methods=['POST', 'DELETE'], detail=True, url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        return self._manage_recipe_relation(
            request, pk, serializers.RecipeShortSerializer, ShoppingCart
        )

    @action(methods=['GET'], detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        content, filename, content_type = build_shopping_cart_file(
            user=request.user,
            file_format=request.query_params.get(
                'file_format', SHOPPING_CART_FORMAT
            ),
        )
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def get_queryset(self):
        user = self.request.user

        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags',
            'ingredients_amounts__ingredient',
        )
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                ),
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeReadSerializer
        return serializers.RecipeWriteSerializer

    def _manage_recipe_relation(
        self, request, recipe_id, serializer_class, relation_model
    ):
        if request.method == 'DELETE':
            self._remove_recipe_relation(
                user=request.user,
                recipe_id=recipe_id,
                relation_model=relation_model,
            )
            return core.SUCCESS_DELETED_RESPONSE

        recipe = self._add_recipe_relation(
            user=request.user,
            recipe_id=recipe_id,
            relation_model=relation_model,
        )
        return Response(
            serializer_class(
                recipe,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def _add_recipe_relation(self, *, user, recipe_id, relation_model):
        """
        Создать связь user<->recipe в relation_model (Favorite/ShoppingCart).
        Возвращает:
        - Recipe (успех)
        - Поднимает исключение ValidationError (ошибка)
        """
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        _, created = relation_model.objects.get_or_create(
            user=user, recipe=recipe
        )
        if not created:
            raise ValidationError(
                core.format_error(
                    core.ERROR_RECIPE_IN_LIST,
                    recipe=recipe.name,
                    list=relation_model.__name__,
                )
            )
        return recipe

    def _remove_recipe_relation(self, *, user, recipe_id, relation_model):
        """
        Удалить связь user<->recipe из relation_model (Favorite/ShoppingCart).
        Возвращает:
        - None (успех)
        - Поднимает исключение ValidationError (ошибка)
        """
        relation_model.objects.filter(user=user, recipe_id=recipe_id).delete()
        return None
