from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe
from recipes.services.short_links import get_id_from_short_link


def short_recipe_redirect(request, code):
    try:
        recipe_id = get_id_from_short_link(code)
    except ValueError:
        raise Http404('Invalid short link')

    recipe = get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/api/recipes/{recipe.id}')
