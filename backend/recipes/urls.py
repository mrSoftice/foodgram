from django.urls import path

from recipes.views import short_link_view

app_name = 'recipes'

urlpatterns = [
    path('s/<int:recipe_id>/', short_link_view, name='short-link-view'),
]
