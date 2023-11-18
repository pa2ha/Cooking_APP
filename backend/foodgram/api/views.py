from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import exceptions, filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredients,
                            Shopping_cart, Tag)
from users.pagination import CustomPageNumberPagination

from .filters import RecipeFilter
from .permissions import IsAuthorOrAdminPermission
from .serializers import (FavoriteSerializer, IngredientsSerializer,
                          RecipeCreateUpdateSerializer, RecipeSerializer,
                          TagSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientsSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)

    def get_queryset(self):
        name_param = self.request.query_params.get('name', None)
        if name_param:
            return Ingredient.objects.filter(name__istartswith=name_param)

        return Ingredient.objects.all()


class RecipesViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminPermission,)
    pagination_class = CustomPageNumberPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method != 'GET':
            return RecipeCreateUpdateSerializer

        return RecipeSerializer

    @action(detail=True, methods=('post', 'delete', "get"))
    def favorite(self, request, pk=None):
        user = self.request.user

        if self.request.method == 'POST':
            try:
                recipe = Recipe.objects.get(pk=pk)
            except Recipe.DoesNotExist:
                raise exceptions.ValidationError(
                    f'Рецепт с id {pk} не найден.'
                    )

            if Favorite.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                raise exceptions.ValidationError('Рецепт уже в избранном.')

            Favorite.objects.create(user=user, recipe=recipe)
            serializer = FavoriteSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'GET':
            is_favorited = Favorite.objects.filter(user=user,
                                                   recipe=recipe).exists()
            return Response({'is_favorited': is_favorited})

        if self.request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
            if not Favorite.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                raise exceptions.ValidationError(
                    'Рецепта нет в избранном, либо он уже удален.'
                )

            favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
            favorite.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=('post', 'delete', "get"))
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        if self.request.method == 'POST':
            try:
                recipe = Recipe.objects.get(pk=pk)
            except Recipe.DoesNotExist:
                raise exceptions.ValidationError(f'Рецепт с id {pk} не найден')
            if Shopping_cart.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                raise exceptions.ValidationError(
                    'Рецепт уже в списке покупок.'
                    )

            Shopping_cart.objects.create(user=user, recipe=recipe)
            serializer = FavoriteSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
            if not Shopping_cart.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                raise exceptions.ValidationError(
                    'Рецепта нет в в списке покупоо, либо он уже удален.'
                )

            favorite = get_object_or_404(Shopping_cart,
                                         user=user,
                                         recipe=recipe)
            favorite.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=('get',))
    def download_shopping_cart(self, request):
        shopping_cart = Shopping_cart.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in shopping_cart]
        buy_list = RecipeIngredients.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient'
        ).annotate(
            amount=Sum('amount')
        )

        buy_list_text = 'Список покупок с сайта Foodgram:\n\n'
        for item in buy_list:
            ingredient = Ingredient.objects.get(pk=item['ingredient'])
            amount = item['amount']
            buy_list_text += (
                f'{ingredient.name}, {amount} '
                f'{ingredient.measurement_unit}\n'
            )

        response = HttpResponse(buy_list_text, content_type="text/plain")
        response['Content-Disposition'] = (
            'attachment; filename=shopping-list.txt'
        )

        return response
