from django_filters.rest_framework import BaseInFilter, CharFilter, FilterSet

from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = BaseInFilter(field_name='tags__slug', lookup_expr='in')
    author = CharFilter(field_name='author__id', lookup_expr='exact')

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
        )
