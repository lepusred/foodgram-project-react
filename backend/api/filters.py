from django_filters import rest_framework
from rest_framework import filters
from recipes.models import Recipe


class RecipeFilter(rest_framework.FilterSet):
    """ Фильтр, используется при отображении рецептов. """
    tags = rest_framework.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = rest_framework.BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = rest_framework.BooleanFilter(
        field_name='is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author')


class CustomSearchFilter(filters.SearchFilter):
    search_param = "name"