from django.http import Http404
from django.shortcuts import redirect

from recipes.models import Recipe


def short_link_view(request, recipe_id):
    if not Recipe.objects.filter(id=recipe_id).exists():
        raise Http404(f'Рецепта с id={recipe_id} не существует')
    return redirect(f'/recipes/{recipe_id}/')
