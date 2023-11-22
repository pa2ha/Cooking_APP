# filters.py
import django_filters
from django.db.models import Count

from .models import User


class UserFilter(django_filters.FilterSet):
    recipes_limit = django_filters.NumberFilter(
        method='filter_recipes_limit',
        label='Recipes Limit'
    )

    def filter_recipes_limit(self, queryset, name, value):
        # Фильтруем пользователей по количеству рецептов
        queryset = queryset.annotate(recipes_count=Count('recipes'))
        
        # Проверяем, что recipes_count существует перед фильтрацией
        if 'recipes_count' in queryset.model.__dict__:
            queryset = queryset.filter(recipes_count__lte=value)

        return queryset

    class Meta:
        model = User
        fields = []
