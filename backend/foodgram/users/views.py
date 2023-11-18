from rest_framework import exceptions, status, viewsets
from .serializers import (CustomUserSerializer,
                          CustomUserCreateSerializer,
                          ChangePasswordSerializer,
                          SubscriptionSerializer,
                          UserLoginSerializer)
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Subscription
from django.shortcuts import get_object_or_404
from rest_framework.permissions import (IsAuthenticated,
                                        AllowAny)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from .pagination import CustomPageNumberPagination
User = get_user_model()


class CustomUserViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.action in ('create',):
            return CustomUserCreateSerializer
        if self.request.method == 'GET':
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

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk=None):
        user = self.request.user
        author_id = request.data.get('id', pk)
        author = get_object_or_404(User, pk=author_id)
        if self.request.method == 'POST':
            if user == author:
                raise exceptions.ValidationError(
                    'Подписка на самого себя запрещена.'
                )
            if Subscription.objects.filter(
                user=user,
                author=author
            ).exists():
                raise exceptions.ValidationError('Подписка уже оформлена.')
            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(author,
                                                context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            if not Subscription.objects.filter(
                user=user,
                author=author
            ).exists():
                raise exceptions.ValidationError(
                    'Подписка не была оформлена, либо уже удалена.'
                )

            subscription = get_object_or_404(
                Subscription,
                user=user,
                author=author
            )
            subscription.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=("get",),
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request, pk=None):
        user = self.request.user
        user_subscriptions = user.subscribes.all()
        authors = [item.author.id for item in user_subscriptions]
        queryset = User.objects.filter(id__in=authors)
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
