from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from django.utils.http import urlencode

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


class RecipesCountAdminMixin:
    recipes_count_lookup = ''
    recipes_count_alias = 'recipes_count'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not self.recipes_count_lookup:
            return qs
        return qs.annotate(
            **{
                self.recipes_count_alias: Count(
                    self.recipes_count_lookup, distinct=True
                )
            }
        )

    @admin.display(description='рецептов')
    def recipes_count(self, obj):
        return getattr(obj, self.recipes_count_alias, 0)


@admin.register(Tag)
class TagAdmin(RecipesCountAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipes_count')
    search_fields = ('name', 'slug')
    recipes_count_lookup = 'recipes'


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    search_fields = (
        'name',
        'measurement_unit',
    )
    list_filter = ('measurement_unit',)
    recipes_count_lookup = 'in_recipes__recipe'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(RecipesCountAdminMixin, admin.ModelAdmin):
    list_select_related = ('author',)
    list_display = ('name', 'author', 'favorites_count')
    search_fields = (
        'name__search',
        'author__username',
        'tags__name',
        'ingredients__name',
    )
    list_filter = ('tags', 'author')
    filter_horizontal = ('tags',)
    readonly_fields = ('favorites_count',)

    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.in_favorites.count()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.select_related('author')
            .prefetch_related('tags')
            .annotate(favorites_total=Count('in_favorites', distinct=True))
        )


@admin.register(User)
class UserAdmin(RecipesCountAdminMixin, UserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'full_name',
        'recipes_count',
        'subscribers_count',
        'subscriptions_count',
        'avatar_preview',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )

    readonly_fields = ('avatar_preview',)
    recipes_count_lookup = 'recipes'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            subscriptions_total=Count('subscriptions', distinct=True),
            subscribers_total=Count('authors', distinct=True),
        )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.last_name} {user.first_name}'

    @mark_safe
    @admin.display(description='Аватар')
    def avatar_preview(self, obj):
        if obj.avatar:
            return (
                f'<a href="{obj.avatar.url}" target="_blank" rel="noopener">'
                f'<img src="{obj.avatar.url}" style="height:40px; width:40px; '
                f'object-fit:cover; border-radius:50%;" />'
                f'</a>'
            )
        return '-'

    def _subscription_changelist_link(
        self, *, label: str, filter_key: str, user_id: int, value: int
    ):
        url = reverse(
            f'admin:{Subscription._meta.app_label}_{Subscription._meta.model_name}_changelist'
        )
        query = urlencode({filter_key: user_id})
        return format_html('<a href="{}?{}">{}</a>', url, query, value)

    @admin.display(description='Подписок', ordering='subscriptions_total')
    def subscriptions_count(self, obj):
        return self._subscription_changelist_link(
            label='Подписок',
            filter_key='user__id__exact',  # user = obj (на кого подписан)
            user_id=obj.id,
            value=obj.subscriptions_total,
        )

    @admin.display(description='Подписчиков', ordering='subscribers_total')
    def subscribers_count(self, obj):
        # return obj.subscribers_total
        return self._subscription_changelist_link(
            label='Подписчиков',
            filter_key='author__id__exact',  # author = obj (кто подписан)
            user_id=obj.id,
            value=obj.subscribers_total,
        )


@admin.register(Favorite, ShoppingCart)
class RelationsAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = (
        'user__email',
        'user__username',
        'author__email',
        'author__username',
    )
