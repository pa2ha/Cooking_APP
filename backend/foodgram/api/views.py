from django.db.models import F, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientsFilter, RecipeFilter
from api.permissions import IsAuthorOrAdminPermission
from api.serializers import (FavoriteCreateSerializer,
                             FavoriteDeleteSerializer, IngredientsSerializer,
                             RecipeCreateUpdateSerializer, RecipeSerializer,
                             ShoppingCartCreateSerializer,
                             ShoppingCartDeleteSerializer, TagSerializer)
from recipes.models import Ingredient, Recipe, RecipeIngredients, Tag
from users.pagination import CustomPageNumberPagination

from .utils import generate_pdf


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientsSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientsFilter


class RecipesViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    pagination_class = CustomPageNumberPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method != 'GET':
            return RecipeCreateUpdateSerializer

        return RecipeSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return (AllowAny(),)
        return (IsAuthorOrAdminPermission(),)

    @staticmethod
    def handle_create_request(
        serializer_class, serializer_data, status_code, request
    ):
        serializer = serializer_class(
            data=serializer_data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status_code)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def handle_delete_request(
        serializer_class, serializer_data, status_code, request
    ):
        serializer = serializer_class(
            data=serializer_data, context={'request': request})

        if serializer.is_valid():
            serializer.delete(serializer.validated_data)
            return Response(status=status_code)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_data(self, pk):
        return {'recipe_id': pk}

    @action(detail=True,
            permission_classes=[IsAuthenticated], methods=['POST'])
    def favorite(self, request, pk):
        serializer_data = self.get_serializer_data(pk)
        return self.handle_create_request(
            FavoriteCreateSerializer,
            serializer_data, status.HTTP_201_CREATED, request)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        serializer_data = self.get_serializer_data(pk)
        return self.handle_delete_request(
            FavoriteDeleteSerializer,
            serializer_data, status.HTTP_204_NO_CONTENT, request)

    @action(detail=True,
            permission_classes=[IsAuthenticated], methods=['POST'])
    def shopping_cart(self, request, pk=None):
        serializer_data = self.get_serializer_data(pk)
        return self.handle_create_request(
            ShoppingCartCreateSerializer,
            serializer_data, status.HTTP_201_CREATED, request)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        serializer_data = self.get_serializer_data(pk)
        return self.handle_delete_request(
            ShoppingCartDeleteSerializer,
            serializer_data, status.HTTP_204_NO_CONTENT, request)

    @action(detail=False, methods=('get',))
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredients.objects.filter(
            recipe__in_shopping_cart__user=request.user
        ).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        ).order_by('name').annotate(total=Sum('amount'))
        return generate_pdf(ingredients)
