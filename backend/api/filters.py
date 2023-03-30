from django_filters import rest_framework
from rest_framework import filters

from recipes.models import Recipe, Tag


class RecipesFilter(rest_framework.FilterSet):
    """Кастомизация фильтров для рецептов."""

    is_favorited = rest_framework.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    author = rest_framework.NumberFilter(
        field_name='author__id',
        lookup_expr='exact'
    )
    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(
                shopping_cart_recipe__user=self.request.user)
        return queryset


class IngredientSearch(filters.SearchFilter):
    """Кастомизация поиска по ингредиентам."""
    search_param = 'name'
