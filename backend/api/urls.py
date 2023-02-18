from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, MyUserViewSet, RecipeViewSet, TagViewSet

app_name = 'api'

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
]

router = DefaultRouter()
router.register('users', MyUserViewSet)
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
urlpatterns += router.urls
