from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import Recipe
from rest_framework import serializers
from users.models import Subscription

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed'
    )

    def get_is_subscribed(self, obj):
        user = self.context.get('request', None)
        if user and user.user.is_authenticated:
            return Subscription.objects.filter(
                user=user.user, author=obj).exists()
        return False

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed')


class CustomUserCreateSerializer(UserCreateSerializer):
    first_name = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    last_name = serializers.CharField(required=True, max_length=150)

    class Meta:

        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'password')

    def validate_email(self, value):

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Этот email уже используется.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    model = User
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class SubRecipesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', "image", "cooking_time")


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count'
    )

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj)

        recipes_limit = self.context.get(
            'request').query_params.get('recipes_limit')
        if recipes_limit and recipes_limit.isdigit():
            recipes_limit = int(recipes_limit)
            recipes = recipes[:recipes_limit]

        if recipes:
            serializer = SubRecipesSerializer(
                recipes,
                context={'request': self.context.get('request')},
                many=True
            )
            return serializer.data

        return []

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request', None)
        limit = request.query_params.get('recipes_limit') if request else None
        data['recipes'] = data.get(
            'recipes', {}) if limit and limit.isdigit() else data['recipes']
        return data

    def validate(self, data):
        user = self.context['request'].user
        author_id = self.context['request'].data.get('id')
        author = get_object_or_404(User, pk=author_id)

        if user == author:
            raise serializers.ValidationError(
                'Подписка на самого себя запрещена.')

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError('Подписка уже оформлена.')

        # Проверка наличия подписки перед удалением
        if self.context['request'].method == 'DELETE':
            if not Subscription.objects.filter(
                user=user, author=author).exists(
            ):
                raise serializers.ValidationError(
                    'Подписка не была оформлена, либо уже удалена.')

        return data

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'recipes', 'recipes_count')


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                if user.check_password(password):
                    return attrs
            raise serializers.ValidationError(
                'Неверный email/password')
        raise serializers.ValidationError(
            'Укажите email и password')


class SubscriptionCreateSerializer(serializers.Serializer):
    author_id = serializers.IntegerField()

    def validate_author_id(self, value):
        request = self.context.get('request')
        user = request.user

        if user.id == value:
            raise serializers.ValidationError(
                'Зачем подписываться самому на себя?.')

        return value

    def validate(self, data):
        user = self.context['request'].user
        author_id = data.get('author_id')
        author = get_object_or_404(User, pk=author_id)

        if user == author:
            raise serializers.ValidationError(
                'Подписка на самого себя запрещена.')

        if Subscription.objects.filter(user=user, author=author).exists():
            if self.context['request'].method == 'POST':
                raise serializers.ValidationError('Подписка уже оформлена.')

        if self.context['request'].method == 'DELETE':
            if not Subscription.objects.filter(
                user=user, author=author).exists(
            ):
                raise serializers.ValidationError(
                    'Подписка не была оформлена, либо уже удалена.')

        return data

    def to_representation(self, instance):
        serializer = SubscriptionSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data
