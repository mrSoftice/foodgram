from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe


def short_link_view(request, recipe_id):
    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe_id}/')
