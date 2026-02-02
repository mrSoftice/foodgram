from django.shortcuts import redirect


def short_recipe_redirect(request, recipe_id):
    return redirect(f'/recipes/{recipe_id}/')
