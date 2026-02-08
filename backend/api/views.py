from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
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
from recipes.services import subscriptions
from recipes.services.shopping_cart import (
    get_shopping_cart_ingredients,
    get_shopping_cart_recipes,
    render_as_txt,
)

User = get_user_model()

ERROR_RECIPE_IN_LIST = 'Рецепт {recipe} уже есть в {list}.'
ERROR_ALREADY_SUBSCRIBED = 'Вы уже подписаны на  автора {author}.'


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
            serializers.AuthorWithRecipesSerializer(
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

        _, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author,
        )
        if not created:
            raise ValidationError(
                {
                    'detail': ERROR_ALREADY_SUBSCRIBED.format(
                        author=author.username
                    )
                }
            )
        return Response(
            serializers.AuthorWithRecipesSerializer(
                author, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        get_object_or_404(
            Subscription, user=request.user, author__id=id
        ).delete()
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
        if not Recipe.objects.filter(pk=pk).exists():
            raise NotFound(f'Рецепт с кодом {pk} не найден.')
        return Response(
            {
                'short-link': request.build_absolute_uri(
                    reverse('recipes:short-link-view', args=[pk])
                )
            }
        )

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        url_path='favorite',
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._manage_recipe_relation(request, pk, Favorite)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._manage_recipe_relation(request, pk, ShoppingCart)

    @action(
        methods=['GET'],
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        return FileResponse(
            render_as_txt(
                {
                    'ingredients': get_shopping_cart_ingredients(request.user),
                    'recipes': get_shopping_cart_recipes(request.user),
                }
            ),
            as_attachment=True,
            content_type='text/plain;',
            filename='shopping_cart.txt',
        )

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
        return queryset.order_by('-pub_date')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeReadSerializer
        return serializers.RecipeWriteSerializer

    def _manage_recipe_relation(self, request, recipe_id, relation_model):
        if request.method == 'DELETE':
            get_object_or_404(
                relation_model,
                user=request.user,
                recipe_id=recipe_id,
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        recipe = get_object_or_404(Recipe, pk=recipe_id)
        _, created = relation_model.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if not created:
            raise ValidationError(
                {
                    'detail': ERROR_RECIPE_IN_LIST.format(
                        recipe=recipe.name,
                        list=relation_model._meta.verbose_name,
                    )
                }
            )
        return Response(
            serializers.RecipeShortSerializer(
                recipe,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )
