from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotAuthenticated, ValidationError

from recipes.models import Recipe
from recipes.services import core


def add_recipe_relation(*, user, recipe_id, relation_model):
    """
    Создать связь user<->recipe в relation_model (Favorite/ShoppingCart).
    Возвращает:
      - Recipe (успех)
      - Поднимает исключение ValidationError (ошибка)
    """
    if user.is_anonymous:
        raise NotAuthenticated(detail=core.ERROR_UNAUTHORIZED)

    recipe = get_object_or_404(Recipe, pk=recipe_id)
    _, created = core.get_or_create_model_instance(
        relation_model, user=user, recipe=recipe
    )
    if not created:
        raise ValidationError(core.ERROR_RECIPE_IN_LIST)
    return recipe


def remove_recipe_relation(*, user, recipe_id, relation_model):
    """
    Удалить связь user<->recipe из relation_model (Favorite/ShoppingCart).
    Возвращает:
      - None (успех)
      - Поднимает исключение ValidationError (ошибка)
    """
    if user.is_anonymous:
        raise NotAuthenticated(detail=core.ERROR_UNAUTHORIZED)

    recipe = get_object_or_404(Recipe, pk=recipe_id)
    deleted_count, _ = relation_model.objects.filter(
        user=user, recipe=recipe
    ).delete()
    if deleted_count == 0:
        raise ValidationError(core.ERROR_RECIPE_NOT_IN_LIST)
    return None
