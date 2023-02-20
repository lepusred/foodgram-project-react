from typing import Type

from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.db.models import Count, Exists, OuterRef, Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (Favorite, Follow, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)
from users.models import User

from .filters import CustomSearchFilter, RecipeFilter
from .permissions import AuthorPermission, ReadOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, MyUserAndRecipeSerializer,
                          ReadRecipeSerializer, TagSerializer,
                          WriteRecipeSerializer)


class MyUserViewSet(UserViewSet):
    """Вьюсет для эндпоинтов пользователя."""
    serializer_class = settings.SERIALIZERS.user
    queryset = User.objects.all()
    permission_classes = settings.PERMISSIONS.user
    token_generator = default_token_generator
    lookup_field = settings.USER_ID_FIELD

    @action(methods=['GET'], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(methods=['GET'], detail=False, serializer_class=MyUserAndRecipeSerializer,
            permission_classes=[IsAuthenticated,])
    def subscriptions(self, request, *args, **kwargs):
        return self.list(self.get_queryset())

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            if self.action == 'subscriptions':
                return User.objects.annotate(
                    is_subscribed=Exists(Follow.objects.filter(
                        user=self.request.user, author=OuterRef('id'))),
                    recipes_count=Count('recipes')).filter(is_subscribed=True)
            return User.objects.annotate(
                is_subscribed=Exists(Follow.objects.filter(
                    user=self.request.user, author=OuterRef('id'))))
        return queryset

    def get_permissions(self):
        if self.action == 'retrieve':
            return (ReadOnly(),)
        return super().get_permissions()

    @action(methods=['POST', 'DELETE'], detail=True, serializer_class=FollowSerializer,
            permission_classes=[IsAuthenticated,])
    def subscribe(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        is_exists = Follow.objects.filter(
            user=self.request.user, author=author).exists()
        if request.method == 'POST':
            if self.request.user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на себя'}, status.HTTP_400_BAD_REQUEST)
            if is_exists:
                return Response(
                    {'errors': 'Подписка на автора оформлена ранее!'}, status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user, author=author)
            instance = User.objects.annotate(
                is_subscribed=Exists(Follow.objects.filter(
                    user=self.request.user, author=author)),
                recipes_count=Count('recipes')).get(id=author.id)
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            if not is_exists:
                return Response(
                    {'errors': 'Вы не были подписаны на этого автора'}, status.HTTP_400_BAD_REQUEST)
            Follow.objects.get(user=self.request.user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    search_fields = ('^name',)
    filter_backends = (CustomSearchFilter,)


class RecipeViewSet(ModelViewSet):
    """Вьюсет рецепта."""
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    ordering = ('pub_date',)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    filterset_class = (RecipeFilter)
    lookup_field = Recipe._meta.pk.name

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return (AllowAny(),)
        elif self.action in ['create', 'favorite', 'shopping_cart', 'download_shopping_cart']:
            return (IsAuthenticated(),)
        elif self.action in ['partial_update', 'destroy']:
            return (AuthorPermission(),)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return WriteRecipeSerializer
        if self.action in ['favorite', 'shopping_cart']:
            return FavoriteSerializer
        return ReadRecipeSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            recipes = Recipe.objects.all()
            recipes.annotate(is_subscribed=Exists(Follow.objects.filter(
                user=self.request.user, author=recipes.values('author'))))
            return recipes.annotate(
                is_favorited=Exists(Favorite.objects.filter(
                    user=self.request.user, recipe=OuterRef('id'))),
                is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                    user=self.request.user, recipe=OuterRef('id')))
            )

        return super().get_queryset()

    def _add_to_shopping_or_favorite(
            self, Model: Type[models.base.ModelBase], request, word, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('id'))
        is_exists = Model.objects.filter(
            user=self.request.user, recipe=recipe).exists()
        if request.method == 'POST':
            if is_exists:
                return Response(
                    {'errors': f'Этот рецепт уже в {word}'}, status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(self.get_object())
            Model.objects.create(user=self.request.user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            if not is_exists:
                return Response(
                    {'errors': f'Этого рецепта не было в {word}'}, status.HTTP_400_BAD_REQUEST)
            Model.objects.get(user=self.request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'], detail=True)
    def favorite(self, request, *args, **kwargs):
        return self._add_to_shopping_or_favorite(
            Favorite, request, 'избранном', *args, **kwargs)

    @action(methods=['POST', 'DELETE'], detail=True)
    def shopping_cart(self, request, *args, **kwargs):
        return self._add_to_shopping_or_favorite(
            ShoppingCart, request, 'списке покупок', *args, **kwargs)

    # скачать спискок покупок
    @action(methods=['GET'], detail=False)
    def download_shopping_cart(self, request, *args, **kwargs):
        user = request.user
        ing = 'Список покупок: '
        ingredients_list = IngredientRecipe.objects.filter(
            recipe__selected_recipe_cart__user=user).values(
            'ingredients__name',
            'ingredients__measurement_unit').annotate(
            Sum('amount'))
        for item in ingredients_list:
            ing += f"{item['ingredients__name']} ({item['ingredients__measurement_unit']}) - {str(item['amount__sum'])} ; "
        return Response(ing, content_type='text/plain')
