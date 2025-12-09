from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientsViewSet,
    RecipesViewSet,
    TagViewSet,
    UserViewSet,
)

v1_router = DefaultRouter()
v1_router.register(r'users', UserViewSet, basename='users')
v1_router.register(r'tags', TagViewSet, basename='tags')
v1_router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
v1_router.register(r'recipes', RecipesViewSet, basename='recipes')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    #    path('', include('djoser.urls')),
]

# переопределяем пути djoser
urlpatterns += [
    path('', include(v1_router.urls)),
]
