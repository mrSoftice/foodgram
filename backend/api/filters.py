from django_filters.rest_framework import CharFilter, FilterSet, NumberFilter

from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilters(FilterSet):
    # tags = BaseInFilter(field_name='tags__slug', lookup_expr='in')
    tags = CharFilter(method='filter_tags')
    author = CharFilter(field_name='author__id', lookup_expr='exact')
    is_in_shopping_cart = NumberFilter(method='filter_is_in_shopping_cart')
    is_favorited = NumberFilter(method='filter_is_favorited')

    def filter_tags(self, queryset, name, value):
        tags = self.request.query_params.getlist('tags')
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none() if value == 1 else queryset
        if value == 1:
            return queryset.filter(shoppingcart__user=user)
        return queryset.exclude(shoppingcart__user=user)

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none() if value == 1 else queryset
        if value == 1:
            return queryset.filter(favorites__user=user)
        return queryset.exclude(favorites__user=user)

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
        )
