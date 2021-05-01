from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsAPITest(TestCase):
    """test the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that a user needs to be authorized to access API"""
        resp = self.client.get(TAGS_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITest(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'sample@gmail.com',
            'password123',
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """Test multiple tags are retrieved"""
        Tag.objects.create(user=self.user, name="French")
        Tag.objects.create(user=self.user, name="Spanish")

        response = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            'other@gmail.com',
            'password123',
        )
        Tag.objects.create(user=user2, name="Breakfast")
        tag = Tag.objects.create(user=self.user, name="Italian")

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {'name': 'Test Tag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()      # returns Boolean; True or False

        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Test creating a new Tag with invalid payload"""
        payload = {'name': ''}
        resp = self.client.post(TAGS_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering tags by those assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Dinner')
        tag2 = Tag.objects.create(user=self.user, name='Cocktails')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Beef Tartar',
            time_minutes=15,
            price=5.00
        )
        recipe.tags.add(tag1)

        resp = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertIn(serializer1.data, resp.data)
        self.assertNotIn(serializer2.data, resp.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""
        tag = Tag.objects.create(user=self.user, name='Dinner')
        Tag.objects.create(user=self.user, name='Cocktails')
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
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        resp = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(resp.data), 1)

## response.data returns:
# [ # OrderedDict(
# [ ('id', 5), ('name', 'Italian') ]
# ) ]
