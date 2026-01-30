from django.http import Http404
from django.shortcuts import redirect

from recipes.services.short_links import get_id_from_short_link


def short_recipe_redirect(request, code):
    try:
        recipe_id = get_id_from_short_link(code)
    except ValueError:
        raise Http404('Invalid short link')

    return redirect(f'/recipes/{recipe_id}/')
