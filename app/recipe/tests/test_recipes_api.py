from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')



def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': 8.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def sample_tag(user, name='Veggie Roasts'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='eggs'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def detail_view(recipe_id):
    """return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


class PublicRecipeAPITests(TestCase):
    """Test publicly available Recipe API"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test user authorization is required to access recipe API"""
        resp = self.client.get(RECIPES_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authorized access to the Recipe API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'tester@gmail.com',
            'pass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        resp = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test recipes are limited to authorised user only"""
        user2 = get_user_model().objects.create_user(
            'other@gmail.com',
            'pass123'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        # db request 1: using auth user in API
        resp = self.client.get(RECIPES_URL)

        # db request 2: accessing all records, filtering by auth user
        recipe = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe, many=True)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)
        self.assertEqual(len(resp.data), 1)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_view(recipe.id)
        resp = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(resp.data, serializer.data)


    ### Errors with the below
    def test_create_basic_recipe(self):
        """Test creating a recipe by itself"""
        payload = {
            'title': 'Carbonara',
            'time_minutes': 45,
            'price': 13.00
        }
        resp = self.client.post(RECIPES_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=resp.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe and tags."""
        tag1 = sample_tag(user=self.user, name="Fish")
        tag2 = sample_tag(user=self.user, name="Stew")
        payload = {
            'title': 'Carbonara',
            'time_minutes': 45,
            'tags': [tag1.id, tag2.id],
            'price': 13.00
        }


        resp = self.client.post(RECIPES_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=resp.data['id'])
        tags = recipe.tags.all()        # retrieve both tags

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients."""
        ingredient1 = sample_ingredient(user=self.user, name='Salmon')
        ingredient2 = sample_ingredient(user=self.user, name='Salt')
        payload = {
            'title': 'Carbonara',
            'time_minutes': 45,
            'price': 13.00,
            'ingredients': [ingredient1.id, ingredient2.id]
        }

        resp = self.client.post(RECIPES_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=resp.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)
