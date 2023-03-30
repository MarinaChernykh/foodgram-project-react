import io

from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.db.models import Sum
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers, status, viewsets
from reportlab.lib import units, pagesizes
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen import canvas

from users.models import User, Subscription
from recipes.models import (Tag, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Favorite)
from .serializers import (CustomUserSerializer, SubscriptionSerializer,
                          TagSerializer, IngredientSerializer,
                          BaseRecipeSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer)
from .permissions import IsAdminOrReadOnly, IsAuthorOrAdminOrReadOnly
from .pagination import CustomPagination
from .filters import RecipesFilter, IngredientSearch


class CustomUserViewSet(UserViewSet):
    """Действия с пользователями и подписками."""
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    pagination_class = CustomPagination

    def get_permissions(self):
        """Выбор прав доступа для операции."""
        if self.action in [
            'me', 'retrieve', 'set_password',
            'subscriptions', 'subscribe'
        ]:
            return (IsAuthenticated(),)
        if self.action in ['list', 'create']:
            return (AllowAny(),)
        if self.action == 'destroy':
            return (IsAdminOrReadOnly(),)
        return super().get_permissions()

    @action(['get'], detail=False)
    def me(self, request, *args, **kwargs):
        """Страница профиля текущего пользователя."""
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(['get'], detail=False)
    def subscriptions(self, request):
        """Список авторов, на которых подписан пользователь."""
        authors = User.objects.filter(subscription__user=self.request.user)
        page = self.paginate_queryset(authors)
        if page:
            serializer = SubscriptionSerializer(
                page, context={'request': request}, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(
            authors, context={'request': request}, many=True)
        return Response(serializer.data)

    @action(['post', 'delete'], detail=True)
    def subscribe(self, request, id):
        """Добавление/удаление авторов в избранное."""
        author = get_object_or_404(User, id=id)
        user = self.request.user
        if request.method == "POST":
            if author == user:
                raise serializers.ValidationError(
                    'Нельзя подписываться на самого себя!')
            if user.subscribed.filter(author=author).exists():
                raise serializers.ValidationError(
                    'Вы уже подписаны на этого автора')
            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = user.subscribed.filter(author=author)
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise serializers.ValidationError(
            'Вы не были подписаны на этого автора')


class TagViewSet(viewsets.ModelViewSet):
    """Отображение тегов."""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Отображение ингредиентов."""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = (IngredientSearch,)
    search_fields = ('^name',)
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Действия с рецептами."""
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter
    pagination_class = CustomPagination

    def get_serializer_class(self):
        """Выбор сериализатора для действий по эндпойнту recipes."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_permissions(self):
        """Выбор прав доступа для операции."""
        if self.action in ['favorite', 'shopping_cart',
                           'download_shopping_cart']:
            return (IsAuthenticated(),)
        return (IsAuthorOrAdminOrReadOnly(),)

    def add_object(self, model, user, recipe):
        """Добавление рецепта в избранное или список покупок."""
        if model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже был добавлен ранее')
        model.objects.create(user=user, recipe=recipe)
        serializer = BaseRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_object(self, model, user, recipe):
        """Удаление рецепта из избранного или списка покупок."""
        obj = model.objects.filter(user=user, recipe=recipe)
        if obj:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise serializers.ValidationError('Указанного рецепта нет в списке')

    @action(['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        """Работа со списком избранных рецептов."""
        recipe = get_object_or_404(Recipe, pk=pk)
        request_data = (Favorite, self.request.user, recipe)
        if request.method == "POST":
            return self.add_object(*request_data)
        return self.delete_object(*request_data)

    @action(['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk):
        """Работа со списком покупок (добавление и удаление)."""
        recipe = get_object_or_404(Recipe, pk=pk)
        request_data = (ShoppingCart, self.request.user, recipe)
        if request.method == "POST":
            return self.add_object(*request_data)
        return self.delete_object(*request_data)

    @action(['get'], detail=False)
    def download_shopping_cart(self, request):
        """Скачивание PDF-файла со списком покупок"""
        products_to_buy = RecipeIngredient.objects.filter(
            recipe__shopping_cart_recipe__user=request.user).values(
                'ingredient__name', 'ingredient__measurement_unit').annotate(
                    quantity=Sum('amount'))
        if products_to_buy:
            buffer = io.BytesIO()
            font_path = settings.FONT_PATH
            pdfmetrics.registerFont(ttfonts.TTFont('Arial', font_path))
            template = canvas.Canvas(buffer, pagesize=pagesizes.A4, bottomup=0)
            textobject = template.beginText()
            textobject.setTextOrigin(2 * units.cm, 2 * units.cm)
            textobject.setFont("Arial", 14)
            textobject.textLine('СПИСОК ПОКУПОК:')
            textobject.moveCursor(0, 14)
            for product in products_to_buy:
                item = (f"{product['ingredient__name']} "
                        f"({product['ingredient__measurement_unit']}) - "
                        f"{product['quantity']}")
                textobject.textLine(item)
            template.drawText(textobject)
            template.showPage()
            template.save()
            buffer.seek(0)
            return FileResponse(
                buffer, as_attachment=True, filename='shopping-list.pdf')
        raise serializers.ValidationError(
            'Сначала добавьте рецепты в список покупок')
