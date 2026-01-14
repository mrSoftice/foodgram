from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Prefetch
from django.forms import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api import filters, pagination, serializers
from api.permissions import IsAuthorOrReadOnly
from foodgram.settings import SHOPPING_CART_FORMAT, USER_SELFINFO_PATH
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from recipes.services import core, relations, subscriptions
from recipes.services.shopping_cart import build_shopping_cart_file
from recipes.services.short_links import get_short_link

User = get_user_model()


def service_exc_to_response(exc):
    return Response(exc.detail, status=exc.status_code)


def build_file_response(file_content, filename, content_type):
    response = HttpResponse(file_content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    lookup_field = 'id'
    permission_classes = (AllowAny,)
    pagination_class = pagination.PageLimitPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return (AllowAny(),)
        return (IsAuthenticated(),)

    def get_queryset(self):
        return subscriptions.annotate_is_subscribed(
            super().get_queryset(), self.request.user
        )

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
        author = subscriptions.get_author_or_404(id)

        try:
            subscriptions.subscribe(request.user, author)
        except (ValidationError, NotAuthenticated) as e:
            return service_exc_to_response(e)

        return Response(
            serializers.SubscribtionReadSerializer(
                author, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        author = subscriptions.get_author_or_404(id)
        try:
            subscriptions.unsubscribe(request.user, author)
        except (ValidationError, NotAuthenticated) as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
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
        recipe = get_object_or_404(Recipe, pk=pk)

        short_link = get_short_link(recipe.id, request)

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
        try:
            content, filename, content_type = build_shopping_cart_file(
                user=request.user,
                file_format=request.query_params.get(
                    'file_format', SHOPPING_CART_FORMAT
                ),
            )
        except (ValidationError, NotAuthenticated) as e:
            return Response(e.detail, status=e.status_code)

        return build_file_response(content, filename, content_type)

    def get_queryset(self):
        user = self.request.user

        author_queryset = subscriptions.annotate_is_subscribed(
            User.objects.all(), user
        )

        queryset = Recipe.objects.all().prefetch_related(
            Prefetch('author', queryset=author_queryset),
            'tags',
            'recipe_ingredients__ingredient__measurement_unit',
            'recipe_ingredients__measurement_unit',
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
        try:
            if request.method == 'POST':
                recipe = relations.add_recipe_relation(
                    user=request.user,
                    recipe_id=recipe_id,
                    relation_model=relation_model,
                )
                serializer = serializer_class(
                    # data={'user': request.user.id, 'recipe': recipe.id},
                    recipe,
                    context={'request': request},
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED,
                )
            # DELETE
            relations.remove_recipe_relation(
                user=request.user,
                recipe_id=recipe_id,
                relation_model=relation_model,
            )
            return core.SUCCESS_DELETED_RESPONSE
        except (ValidationError, NotAuthenticated) as e:
            return service_exc_to_response(e)
