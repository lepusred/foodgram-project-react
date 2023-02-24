import base64

from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from rest_framework import serializers

from recipes.models import (Follow, Ingredient, IngredientRecipe, Recipe, Tag,
                            TagRecipe)
from users.models import User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            if data.startswith('data:image'):
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr),
                                   name='temp.' + ext)
        return super().to_internal_value(data)


class MyUserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""
    is_subscribed = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'id',
            'first_name',
            'last_name',
            'is_subscribed',
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Этот сериализатор используется для записи рецепта."""
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount', 'recipe')

    def validate_date(self, data):
        if data['ingredients'] is None:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент')
        return data


class ReadTagRecipeSerializer(serializers.ModelSerializer):
    """Этот сериализатор используется для отображения тегов при чтении
    рецептов."""
    id = serializers.StringRelatedField(read_only=True, source='tags.id')
    name = serializers.StringRelatedField(read_only=True, source='tags.name')
    slug = serializers.StringRelatedField(read_only=True, source='tags.slug')
    color = serializers.StringRelatedField(read_only=True, source='tags.color')

    class Meta:
        model = IngredientRecipe
        fields = ('name', 'id', 'color', 'slug')

# аналогично предыдущему


class ReadIngredientRecipeSerializer(serializers.ModelSerializer):
    """Этот сериализатор используется для отображения ингредиентов при чтении
    рецептов."""
    id = serializers.StringRelatedField(
        read_only=True, source='ingredients.id')
    name = serializers.StringRelatedField(
        read_only=True, source='ingredients.name')
    measurement_unit = serializers.StringRelatedField(
        read_only=True, source='ingredients.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('name', 'amount', 'measurement_unit', 'id')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Этот сериализатор используется для чтения рецептов."""
    author = MyUserSerializer(read_only=True)
    image = Base64ImageField(required=True)
    tags = ReadTagRecipeSerializer(many=True, source='tag_recipe')
    ingredients = ReadIngredientRecipeSerializer(many=True, source='recipe')
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    is_subscribed = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'is_in_shopping_cart',
            'is_favorited',
            'image',
            'author',
            'tags',
            'ingredients',
            'name',
            'text',
            'pub_date',
            'cooking_time',
            'is_subscribed')


class WriteRecipeSerializer(serializers.ModelSerializer):
    """Этот сериализатор используется для записи рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    ingredients = IngredientRecipeSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'image',
            'id',
            'cooking_time',
            'text',
            'name',
            'tags')
        read_only_fields = ('pub_date', 'author')

    def creating_ingredient_recipe(self, ingredients, recipe, need_delete):
        # функция для записи или обновления ингредиентов рецепта
        if need_delete:
            IngredientRecipe.objects.filter(recipe=recipe).delete()
        for ingredient in ingredients:
            IngredientRecipe.objects.create(
                ingredients_id=ingredient.pop(
                    'id').id, amount=ingredient.pop('amount'),
                recipe=recipe)

    def creating_tag_recipe(self, tags, recipe, need_delete):
        # функция для записи или обновления тегов рецепта
        if need_delete:
            TagRecipe.objects.filter(recipe=recipe).delete()
        for tag in tags:
            TagRecipe.objects.create(
                tags_id=tag.id, recipe=recipe)

    def pop_it(self, validated_data):
        return (validated_data.pop('ingredients'), validated_data.pop('tags'))

    def create(self, validated_data):
        ingredients, tags = self.pop_it(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        self.creating_ingredient_recipe(ingredients, recipe, False)
        self.creating_tag_recipe(tags, recipe, False)
        return recipe

    def update(self, instance, validated_data):
        ingredients, tags = self.pop_it(validated_data)
        super().update(instance, validated_data)
        self.creating_ingredient_recipe(ingredients, instance, True)
        self.creating_tag_recipe(tags, instance, True)
        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance).data

    def validate_date(self, data):
        if data['cooking_time'] < 1 or isinstance(self.cooking_time, float):
            raise serializers.ValidationError(
                'Время готовки должно быть целым больше 1')
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения данных при добавлении в избранное."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class MyUserAndRecipeSerializer(serializers.ModelSerializer):
    """Агрегирующий сериализатор для отображения данных после подпски на автора
    и при чтении моих подписок."""
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes_count = serializers.IntegerField()

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'id',
            'first_name',
            'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )
    def get_recipes(self, obj):
        page_size = self.context['request'].query_params.get('recipes_limit') or 1
        paginator = Paginator(obj.recipes.all(), page_size)
        page = self.context['request'].query_params.get('page') or 1
        recipes = paginator.page(page)
        serializer = FavoriteSerializer(recipes, many=True)
        return serializer.data

class FollowSerializer(serializers.ModelSerializer):
    """Дополнительный сериализатор, чтобы создать запись при подписке в БД."""
    class Meta:
        model = Follow
        fields = ()

    def to_representation(self, instance):
        return MyUserAndRecipeSerializer(instance).data
