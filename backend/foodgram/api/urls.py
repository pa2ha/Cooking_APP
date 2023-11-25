from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet, custom_obtain_auth_token

from .views import IngredientsViewSet, RecipesViewSet, TagViewSet

v1_router = DefaultRouter()
v1_router.register('tags', TagViewSet)
v1_router.register('ingredients', IngredientsViewSet)
v1_router.register('recipes', RecipesViewSet)
v1_router.register('users', CustomUserViewSet, basename='customuser')


urlpatterns = [
    path('auth/token/login/', custom_obtain_auth_token),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(v1_router.urls)),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
