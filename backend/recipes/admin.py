from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    MeasurementUnit,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
    User,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('measurement_unit')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'ingredient__measurement_unit', 'measurement_unit'
        )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_select_related = [
        'author',
    ]
    list_display = (
        'name',
        'author',
    )
    search_fields = ('name__search', 'author')
    list_filter = ('tags',)
    filter_horizontal = ('tags',)
    readonly_fields = ('favorites_count',)

    inlines = (RecipeIngredientInline,)
    # exclude = ('tags',)

    @admin.display(description='Количество в избранном')
    def favorites_count(self, obj):
        return obj.favorites.count()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('tags')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = (
        'username',
        'email',
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
