from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import Subscription
from users.pagination import CustomPageNumberPagination
from users.serializers import (ChangePasswordSerializer,
                               CustomUserCreateSerializer,
                               CustomUserSerializer,
                               SubscriptionCreateSerializer,
                               SubscriptionSerializer,
                               UserLoginSerializer)

User = get_user_model()


class CustomUserViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.request.method != 'GET':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(detail=False, methods=["get"],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=("post",))
    def set_password(self, request, pk=None):
        user = self.request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            if not user.check_password(
                serializer.data.get("current_password")
            ):
                return Response({"old_password": ["Неверный пароль."]},
                                status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data.get("new_password"))
            user.save()

            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        serializer = SubscriptionCreateSerializer(
            data={'author_id': pk}, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        author_id = pk
        author = get_object_or_404(User, pk=author_id)

        if self.request.method == 'POST':
            Subscription.objects.create(user=user, author=author)
            response_data = SubscriptionCreateSerializer(
                author, context={'request': request}).data
            return Response(response_data, status=status.HTTP_201_CREATED)

        subscription = get_object_or_404(
            Subscription, user=user, author=author)
        subscription.delete()
        return Response({'message': 'Подписка успешно удалена.'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=("get",),
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request, pk=None):
        user = self.request.user
        user_subscriptions = user.subscribes.all()
        authors = [item.author.id for item in user_subscriptions]
        queryset = User.objects.filter(id__in=authors)
        queryset = self.filter_queryset(queryset)
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(paginated_queryset,
                                            many=True,
                                            context={'request': request})
        return self.get_paginated_response(serializer.data)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


custom_obtain_auth_token = CustomAuthToken.as_view()
