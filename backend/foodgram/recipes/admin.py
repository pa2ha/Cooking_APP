from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, Shopping_cart, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class RecipeIngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author', 'in_favorite_count')
    inlines = (RecipeIngredientInline,)
    list_filter = ('name', 'author', 'tags')
    search_fields = ('name',)

    @admin.display(description='В избранном')
    def in_favorite_count(self, obj):
        return obj.in_favorite.count()


@admin.register(Shopping_cart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
