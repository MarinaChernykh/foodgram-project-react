from django.contrib import admin

from .models import (Recipe, Ingredient, RecipeIngredient,
                     Tag, ShoppingCart, Favorite)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline,)
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name',)
    fields = (
        'name', 'text', 'image', 'cooking_time', 'author',
        'tags', 'pub_date', 'in_favorite_count'
    )
    filter_horizontal = ('ingredients', 'tags')
    readonly_fields = ('pub_date', 'in_favorite_count')

    @admin.display(description='Добавления в избранное')
    def in_favorite_count(self, obj):
        return obj.favorite_recipe.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe__name', 'ingredient__name',)
    ordering = ('recipe__id',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(ShoppingCart, Favorite)
class SelectedRecipesAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__name')
    ordering = ('user__id', 'recipe__name')
