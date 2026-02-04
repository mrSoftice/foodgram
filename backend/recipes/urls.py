from django.urls import path

from recipes.views import ShortLinkView

urlpatterns = [
    path(
        's/<int:recipe_id>/', ShortLinkView.as_view(), name='short-link-view'
    ),
]
