from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.forms import ValidationError
from django.http import HttpResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api import filters, pagination, serializers
from api.permissions import IsAuthorOrReadOnly
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from recipes.services import core, relations, subscriptions
from recipes.services.shopping_cart import build_shopping_cart_file
from recipes.services.short_links import get_short_link

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
            serializers.SubscribtionReadSerializer(
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
        author = subscriptions.get_author_or_404(id)

        try:
            subscriptions.subscribe(request.user, author)
        except (ValidationError, NotAuthenticated) as e:
            return Response(e.detail, status=e.status_code)

        return Response(
            serializers.SubscribtionReadSerializer(
                author, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        # author = subscriptions.get_author_or_404(id)
        subscriptions.unsubscribe(request.user, id)
        return core.SUCCESS_DELETED_RESPONSE


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
        short_link = get_short_link(pk, request)

        return Response({'short-link': short_link})

    @action(methods=['POST', 'DELETE'], detail=True, url_path='favorite')
    def favorite(self, request, pk=None):
        return self._manage_recipe_relation(
            request, pk, serializers.RecipeForCartSerializer, Favorite
        )

    @action(methods=['POST', 'DELETE'], detail=True, url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        return self._manage_recipe_relation(
            request, pk, serializers.RecipeForCartSerializer, ShoppingCart
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

        # author_queryset = subscriptions.annotate_is_subscribed(
        #     User.objects.all(), user
        # )

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
        return serializers.RecipeCreateSerializer

    def _manage_recipe_relation(
        self, request, recipe_id, serializer_class, relation_model
    ):
        if request.method == 'DELETE':
            relations.remove_recipe_relation(
                user=request.user,
                recipe_id=recipe_id,
                relation_model=relation_model,
            )
            return core.SUCCESS_DELETED_RESPONSE

        recipe = relations.add_recipe_relation(
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
