from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')



class PublicIngredientAPITest(TestCase):
    """Test publicly available Ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test authenticated login is required to access the ingredients API"""
        resp = self.client.get(INGREDIENTS_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITest(TestCase):
    """Test authenticated access to the Ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email="tester@gmail.com",
            password='pass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        """Test to retrieve ingredients"""
        Ingredient.objects.create(user=self.user, name='carrots')
        Ingredient.objects.create(user=self.user, name='tomatoes')

        resp = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test ingredients retrieved are only from authenticated user's"""
        user2 = get_user_model().objects.create(
            email='other@gmail.com',
            password='pass123'
        )
        Ingredient.objects.create(user=user2, name='Beef')
        ingredient = Ingredient.objects.create(user=self.user, name='onion')

        resp = self.client.get(INGREDIENTS_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(ingredient.name, resp.data[0]['name'])

    def test_create_ingredient_successful(self):
        """Test adding an ingredient works"""
        payload = {'name': 'Olives'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating an ingredient with an empty string fails"""
        payload = {'name': ''}
        resp = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Beef')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Milk')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Beef Tartar',
            time_minutes=15,
            price=5.00
        )
        recipe.ingredients.add(ingredient1)

        resp = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, resp.data)
        self.assertNotIn(serializer2.data, resp.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        ingredient = Ingredient.objects.create(user=self.user, name='Beef')
        Ingredient.objects.create(user=self.user, name='Milk')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Beef Tartar',
            time_minutes=15,
            price=5.00
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Venison salad',
            time_minutes=20,
            price=15.50
        )
        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        resp = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(resp.data), 1)



### serializer:
# IngredientSerializer(<QuerySet [<Ingredient: tomatoes>, <Ingredient: carrots>]>, many=True):
#     id = IntegerField(label='ID', read_only=True)
#     name = CharField(max_length=255)

# resp.data:
# [OrderedDict([('id', 5), ('name', 'tomatoes')]), OrderedDict([('id', 4), ('name', 'carrots')])]