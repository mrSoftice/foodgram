from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    COOKING_TIME_FILTERS = {
        'до 10 мин': (0, 10),
        '10-30 мин': (11, 30),
        '30-60 мин': (31, 60),
        'более 60 мин': (61, 999_999_999),
    }
    alias_map = {
        f't{t0}_{t1}': label
        for label, (t0, t1) in COOKING_TIME_FILTERS.items()
    }
    filter_expressions = {
        f't{t0}_{t1}': (t0, t1) for (t0, t1) in COOKING_TIME_FILTERS.values()
    }
    aggregate_time = {
        key: Count('id', filter=Q(cooking_time__range=q_exp))
        for key, q_exp in filter_expressions.items()
    }

    def lookups(self, request, model_admin):
        recipes = model_admin.get_queryset(request)
        counts = recipes.aggregate(**self.aggregate_time)

        # подписи + (count)
        return tuple(
            (key, f'{self.alias_map[key]} ({counts[key]})')
            for key in self.filter_expressions.keys()
        )

    def queryset(self, request, recipes):
        if self.value() in self.filter_expressions:
            return recipes.filter(
                cooking_time__range=self.filter_expressions[self.value()]
            )
        return recipes


class YesNoFilter(admin.SimpleListFilter):
    title = None
    parameter_name = None
    lookup_choices = (('1', 'да'), ('0', 'нет'))

    filter_field = None
    yes_lookup = 'gt'
    no_lookup = 'exact'

    def lookups(self, request, model_admin):
        return self.lookup_choices

    def queryset(self, request, queryset):
        if not self.filter_field:
            raise ValueError('Необходимо задать filter_field в фильтре.')

        val = self.value()
        if val == '1':
            return queryset.filter(
                **{f'{self.filter_field}__{self.yes_lookup}': 0}
            )
        if val == '0':
            return queryset.filter(
                **{f'{self.filter_field}__{self.no_lookup}': 0}
            )
        return queryset


class HasRecipesFilter(YesNoFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'

    filter_field = 'recipes_count'


class IsInRecipesFilter(YesNoFilter):
    title = 'Есть в рецептах'
    parameter_name = 'is_in_recipes'
    lookup_choices = (('1', 'да'), ('0', 'нет'))

    filter_field = 'recipes_count'


class HasSubscribersFilter(YesNoFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_followers'

    filter_field = 'subscribers_total'


class HasSubscriptionsFilter(YesNoFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'

    filter_field = 'subscriptions_total'


class RecipesCountAdminMixin:
    list_display = ('recipes_count',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(**{'recipes_count': Count('recipes', distinct=True)})
        )

    @admin.display(description='рецептов')
    def recipes_count(self, obj):
        return obj.recipes_count


@admin.register(Tag)
class TagAdmin(RecipesCountAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', *RecipesCountAdminMixin.list_display)
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountAdminMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit',
        *RecipesCountAdminMixin.list_display,
    )
    ordering = ('name',)
    list_display_links = ('name', 'id')
    search_fields = (
        'name',
        'measurement_unit',
    )
    list_filter = (
        IsInRecipesFilter,
        'measurement_unit',
    )


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_select_related = ('author',)
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'tags_list',
        'ingredients_list',
        'image_preview',
        'favorites_count',
    )
    list_display_links = (
        'name',
        'id',
    )
    search_fields = (
        'name',
        'author__username',
        'tags__name',
        'ingredients__name',
    )
    list_filter = (
        'tags',
        ('author', admin.RelatedOnlyFieldListFilter),
        CookingTimeFilter,
    )
    filter_horizontal = ('tags',)
    readonly_fields = ('favorites_count',)

    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @mark_safe
    @admin.display(description='Изображение')
    def image_preview(self, recipe):
        if recipe.image:
            return (
                f'<a href="{recipe.image.url}" target="_blank" rel="noopener">'
                f'<img src="{recipe.image.url}" style="height:60px;width:60px;'
                f'object-fit:cover; border-radius:8px;" />'
                f'</a>'
            )
        return '-'

    @mark_safe
    @admin.display(description='Ингредиенты')
    def ingredients_list(self, recipe):
        return '<br>'.join(recipe.ingredients.values_list('name', flat=True))

    @mark_safe
    @admin.display(description='Теги')
    def tags_list(self, recipe):
        return '<br>'.join(recipe.tags.values_list('name', flat=True))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.select_related('author')
            .prefetch_related('tags')
            .annotate(favorites_total=Count('favorites', distinct=True))
        )


@admin.register(User)
class UserAdmin(RecipesCountAdminMixin, UserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'full_name',
        *RecipesCountAdminMixin.list_display,
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
    list_filter = (
        HasRecipesFilter,
        HasSubscribersFilter,
        HasSubscriptionsFilter,
    )
    list_display_links = (
        'username',
        'id',
        'email',
    )
    readonly_fields = ('avatar_preview',)

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
    def avatar_preview(self, user):
        if user.avatar:
            return (
                f'<a href="{user.avatar.url}" target="_blank" rel="noopener">'
                f'<img src="{user.avatar.url}" style="height:40px;width:40px;'
                f'object-fit:cover; border-radius:50%;" />'
                f'</a>'
            )
        return '-'

    @mark_safe
    def _subscription_changelist_link(
        self, *, label: str, filter_key: str, user_id: int, value: int
    ):
        url = reverse(
            f'admin:{Subscription._meta.app_label}_'
            f'{Subscription._meta.model_name}_changelist'
        )
        query = urlencode({filter_key: user_id})
        return f'<a href="{url}?{query}">{value} {label}</a>'

    @admin.display(description='Подписок', ordering='subscriptions_total')
    def subscriptions_count(self, user):
        return self._subscription_changelist_link(
            label='Подписок',
            filter_key='user__id__exact',  # user = obj (на кого подписан)
            user_id=user.id,
            value=user.subscriptions_total,
        )

    @admin.display(description='Подписчиков', ordering='subscribers_total')
    def subscribers_count(self, user):
        return self._subscription_changelist_link(
            label='Подписчиков',
            filter_key='author__id__exact',  # author = obj (кто подписан)
            user_id=user.id,
            value=user.subscribers_total,
        )


@admin.register(Favorite, ShoppingCart)
class RelationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
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
