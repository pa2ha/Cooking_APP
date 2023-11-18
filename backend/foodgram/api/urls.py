from django.urls import include, path
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.conf import settings
from users.views import CustomUserViewSet

from .views import TagViewSet, IngredientsViewSet, RecipesViewSet
from users.views import custom_obtain_auth_token

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
