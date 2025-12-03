from django_filters.rest_framework import CharFilter, FilterSet

from recipes.models import Ingredient


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
