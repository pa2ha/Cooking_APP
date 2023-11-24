import base64

import webcolors
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredients,
                            Shopping_cart, Tag)
from rest_framework import exceptions, serializers
from users.serializers import CustomUserSerializer


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('__all__')


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('__all__')


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateUpdateRecipeIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Количество ингредиента должно быть 1 или более.'
            ),
        )
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField(
        method_name='get_ingredients'
    )
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_in_shopping_cart'
    )
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Shopping_cart.objects.filter(user=user, recipe=obj).exists()

    def get_ingredients(self, obj):
        ingredients = RecipeIngredients.objects.filter(recipe=obj)
        serializer = RecipeIngredientsSerializer(ingredients, many=True)

        return serializer.data

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=True, allow_null=True)
    ingredients = CreateUpdateRecipeIngredientsSerializer(many=True,
                                                          required=True)
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Время приготовления должно быть 1 или более.'
            ),
        )
    )

    def create_or_update_ingredients(self, instance, ingredients):
        recipe_ingredients = []

        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient_id = ingredient['id']
            ingredient_obj = Ingredient.objects.filter(
                pk=ingredient_id).first()
            if not ingredient_obj:
                raise serializers.ValidationError(
                    f'Ингредиент с id {ingredient_id} не найден.')
            recipe_ingredients.append(
                RecipeIngredients(
                    recipe=instance,
                    ingredient=ingredient_obj,
                    amount=amount
                )
            )
        RecipeIngredients.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)

        self.create_or_update_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags is None:
            raise exceptions.ValidationError(
                'Необходимо предоставить теги для обновления рецепта.')
        if tags is not None:
            instance.tags.set(tags)

        ingredients = validated_data.pop('ingredients', None)
        if ingredients is None:
            raise exceptions.ValidationError(
                'Необходимо предоставить ингредиенты для обновления рецепта.')

        self.create_or_update_ingredients(instance, ingredients)

        return super().update(instance, validated_data)

    def validate_tags(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Добавьте хотя бы один тег'
            )

        tag_ids = set(tag.id for tag in value)
        if len(tag_ids) != len(value):
            raise exceptions.ValidationError('Теги не могут повторяться')

        return value

    def validate_ingredients(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Нужно добавить хотя бы один ингредиент.'
            )
        if 'ingredients' in self.initial_data:
            ingredients = [item['id'] for item in value]
            for ingredient in ingredients:
                if ingredients.count(ingredient) > 1:
                    raise exceptions.ValidationError(
                        'У рецепта не может быть два одинаковых ингредиента.')
        return value

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', "image", "cooking_time")


class FavoriteCreateSerializer(serializers.Serializer):
    recipe_id = serializers.IntegerField()

    def validate_recipe_id(self, value):
        user = self.context['request'].user

        recipe = Recipe.objects.filter(pk=value).first()
        if not recipe:
            raise serializers.ValidationError(f'Рецепт с id {value} не найден')

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном.')

        return value

    def create(self, validated_data):
        user = self.context['request'].user
        recipe_id = validated_data['recipe_id']
        recipe = Recipe.objects.filter(pk=recipe_id).first()
        if not recipe:
            raise serializers.ValidationError(
                f'Рецепт с id {recipe_id} не найден')
        favorite = Favorite.objects.create(user=user, recipe=recipe)
        self.recipe_instance = recipe
        return favorite

    def to_representation(self, instance):
        serializer = FavoriteSerializer(
            self.recipe_instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


class FavoriteDeleteSerializer(serializers.Serializer):
    recipe_id = serializers.IntegerField()

    def validate_recipe_id(self, value):
        recipe = get_object_or_404(Recipe, pk=value)
        user = self.context['request'].user
        if not Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепта нет в избранном, либо он уже удален.')
        return value

    def delete(self, instance):
        user = self.context['request'].user
        recipe = get_object_or_404(Recipe, pk=instance['recipe_id'])
        favorite = Favorite.objects.get(user=user, recipe=recipe)
        favorite.delete()


class ShoppingCartCreateSerializer(serializers.Serializer):
    recipe_id = serializers.IntegerField()

    def validate_recipe_id(self, value):
        recipe = Recipe.objects.filter(pk=value).first()
        if not recipe:
            raise serializers.ValidationError(f'Рецепт с id {value} не найден')
        user = self.context['request'].user
        if Shopping_cart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в списке покупок.')
        self.recipe_instance = recipe
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        recipe_id = validated_data['recipe_id']
        recipe = Recipe.objects.filter(pk=recipe_id).first()
        if not recipe:
            raise serializers.ValidationError(
                f'Рецепт с id {recipe_id} не найден')
        shopping_cart = Shopping_cart.objects.create(user=user, recipe=recipe)
        return shopping_cart

    def to_representation(self, instance):
        serializer = FavoriteSerializer(
            self.recipe_instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


class ShoppingCartDeleteSerializer(serializers.Serializer):
    recipe_id = serializers.IntegerField()

    def validate_recipe_id(self, value):

        recipe = get_object_or_404(Recipe, pk=value)
        user = self.context['request'].user
        if not Shopping_cart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепта нет в списке покупок, либо он уже удален.')
        return value

    def delete(self, instance):
        user = self.context['request'].user
        recipe = get_object_or_404(Recipe, pk=instance['recipe_id'])
        shopping_cart = get_object_or_404(
            Shopping_cart, user=user,
            recipe=recipe)
        shopping_cart.delete()
