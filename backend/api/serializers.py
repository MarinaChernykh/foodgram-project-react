import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from rest_framework import serializers

from users.models import User, Subscription
from recipes.models import (Tag, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Favorite)


class CustomUserSerializer(UserSerializer):
    """Сериализатор для работы с пользователями и подписками."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        if request.user.is_authenticated:
            user_subscriptions = Subscription.objects.filter(user=request.user)
            return user_subscriptions.filter(author=obj.pk).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Обработка данных об ингредиентах для рецепта при GET запросах."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """
    Обработка данных об ингредиентах для рецепта
    при POST и PATCH запросах.
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов при GET запросах."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, read_only=True, source='recipeIngredient')
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time')

    def recipe_status(self, model, obj):
        request = self.context['request']
        if request.user.is_authenticated:
            user_recipes = model.objects.filter(user=request.user)
            return user_recipes.filter(recipe=obj.pk).exists()
        return False

    def get_is_favorited(self, obj):
        return self.recipe_status(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        return self.recipe_status(ShoppingCart, obj)


class Base64ImageField(serializers.ImageField):
    """Обработка изображений."""
    def to_internal_value(self, data):
        if isinstance(data, str) and (data.startswith('data:image')):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов при POST и PATCH запросах."""
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name',
            'text', 'cooking_time', 'author',
        )

    def validate(self, data):
        unique_ingredient_set = set()
        for ingredient in data.get('ingredients'):
            if ingredient.get('id') in unique_ingredient_set:
                raise serializers.ValidationError(
                    'Ингредиент не может быть включен в рецепт несколько раз')
            unique_ingredient_set.add(ingredient.get('id'))
            if ingredient.get('amount') < 1:
                raise serializers.ValidationError(
                    'Количество должно быть более 1')
        return data

    def add_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient.get('id'),
                amount=ingredient.get('amount')
            )

    def add_tags(self, recipe, tags):
        recipe.tags.set(tags)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.add_ingredients(recipe, ingredients)
        self.add_tags(recipe, tags)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        if 'ingredients' in validated_data:
            self.add_ingredients(instance, validated_data.pop('ingredients'))
        if 'tags' in validated_data:
            self.add_tags(instance, validated_data.pop('tags'))
        instance.save()
        return instance

    def to_representation(self, instance):
        context = {'request': self.context['request']}
        return RecipeReadSerializer(instance, context=context).data


class BaseRecipeSerializer(serializers.ModelSerializer):
    """
    Краткая инфо о рецепте для отображения в ответе при
    добавлении рецепта в избранное, список покупок
    и при работе с подписками на авторов.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с подпиской на авторов."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.ReadOnlyField(default=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )
        read_only_fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = BaseRecipeSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
