from django.contrib import admin
from .models import Recipe, Ingredient, Tag


# Регистрируем модель Ingredients
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


# Регистрируем модель Tag
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# Создаем Inline модель для RecipeIngredient
class RecipeIngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


# Создаем Inline модель для RecipeTags
class RecipeTagsInLine(admin.TabularInline):
    model = Recipe.tags.through
    extra = 1


# Регистрируем модель Recipes и добавляем встроенное поле для ингредиентов
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'text', 'pub_date', 'author')
    search_fields = ('name', 'author')
    inlines = (RecipeIngredientInline,)
