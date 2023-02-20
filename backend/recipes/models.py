from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from django.conf import settings


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.TextField(verbose_name='название ингредиента')
    measurement_unit = models.CharField(max_length=150, verbose_name='единицы измерения')

    def __str__(self):
        return f'{self.name},{self.measurement_unit}'

    class Meta:
        verbose_name_plural = 'Ингредиенты'
        verbose_name = 'Ингредиент'


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(max_length=150, verbose_name='название тега')
    slug = models.SlugField(unique=True)
    color = ColorField(default='#FF0000')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Теги'
        verbose_name = 'Тег'


class Recipe(models.Model):
    """Модель рецепта."""
    name = models.CharField(max_length=200, verbose_name="название рецепта")
    text = models.TextField(verbose_name="описание рецепта")
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes'
    )

    image = models.ImageField(
        'Картинка',
        upload_to='recipes/'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe'
    )
    tags = models.ManyToManyField(
        Tag, through='TagRecipe'
    )
    cooking_time = models.IntegerField(validators=(MinValueValidator(1),))

    def __str__(self):
        return f'{self.name}-{self.text[:15]}'

    class Meta:
        ordering = ['-pub_date']
        verbose_name_plural = 'Рецепты'
        verbose_name = 'Рецепт'


class Follow(models.Model):
    """Модель подписок, связывает пользователя и автора."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follower', null=False, blank=False
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        constraints = (models.UniqueConstraint(
            fields=['user', 'author'],
            name='user_to_author_follow',
        ), models.CheckConstraint(check=~Q(author=F('user')),
                                  name='following_himself'),)

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class IngredientRecipe(models.Model):
    """Модель manytomany связывает ингредиент и рецепт."""
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        null=False,
        related_name='ingredients')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=False,
        related_name='recipe')
    amount = models.FloatField(null=False)


class TagRecipe(models.Model):
    """Модель manytomany связывает тег и рецепт."""
    tags = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='tags')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='tag_recipe')

    def __str__(self):
        return f'{self.tags} {self.recipe}'


class Favorite(models.Model):
    """Модель избранное связывает пользователя и рецепт."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='selector', null=False, blank=False
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='selected_recipe'
    )

    class Meta:
        constraints = (models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='user_to_recipe_favorite',
        ),)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(models.Model):
    """Модель список покупок связывает пользователя и рецепт."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='selector_cart', null=False, blank=False
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='selected_recipe_cart'
    )

    class Meta:
        constraints = (models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='user_to_recipe_in_shoppingcart',
        ),)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
