from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api import filters, pagination, serializers
from api.permissions import IsAuthorOrReadOnly
from foodgram.settings import USER_SELFINFO_PATH
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag

User = get_user_model()


class UserViewSet(ModelViewSet):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()
    lookup_field = 'id'
    permission_classes = (AllowAny,)

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return (AllowAny(),)
        return (IsAuthenticated(),)

    @action(methods=['GET'], detail=False, url_path=USER_SELFINFO_PATH)
    def me(self, request):
        serializer = serializers.UserSerializer(request.user)
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
    )
    def avatar(self, request): ...

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
        pagination_class=[pagination.PageLimitPagination],
    )
    def subscriptions(self, request):
        serializer = serializers.SubscribtionReadSerializer(
            User.objects.filter(followers__user=request.user),
            many=True,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        subscription = get_object_or_404(
            request.user.subscriptions, author=author
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
    filterset_class = filters.RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        user = self.request.user
        base_queryset = (
            Recipe.objects.all()
            .select_related('author')
            .prefetch_related(
                'tags',
                'recipe_ingredients__ingredient__measurement_unit',
                'recipe_ingredients__measurement_unit',
            )
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
