from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from .models import Subscription
from recipes.models import Recipe

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
        return SubRecipesSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request', None)
        if request:
            limit = request.query_params.get('recipes_limit')
            if limit is not None and limit.isdigit():
                data['recipes'] = data['recipes'][:int(limit)]
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
