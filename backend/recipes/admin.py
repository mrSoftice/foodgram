from django.contrib import admin

from .models import Ingredient, MeasurementUnit, Recipe, Tag, User


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


class TagsInline(admin.StackedInline):
    model = Recipe.tags.through
    extra = 1


@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
    )
    search_fields = ('name__search', 'author')
    list_filter = ('tags',)

    filter_horizontal = ('tags',)
    readonly_fields = ('favorites_count',)
    # inlines = (TagsInline,)
    # exclude = ('tags',)

    @admin.display(description='Количество в избранном')
    def favorites_count(self, obj):
        return obj.favorites.count()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = (
        'username',
        'email',
    )
