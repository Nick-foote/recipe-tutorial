from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from core import models


def sample_user(email='sample@gmail.com', password='sample123'):
    """Creates sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTest(TestCase):
    def test_create_user_with_email(self):
        email = 'test@gmail.com'
        password = 'pass1234'
        # username = 'TestUser'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            # username=username,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_super_user(self):
        user = get_user_model().objects.create_superuser(
            'test@gmail.com',
            'pass123'
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_new_user_email_normalised(self):
        email = 'test@GMAIL.COM'
        user = get_user_model().objects.create_user(email, 'password123')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Creating a user with an invalid email should raise an error."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'pass123')

    def test_tag_str(self):
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Korean',
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredients(self):
        """test ingredient string representation"""
        ingredient = models.Ingredient.objects.create(
            name="Garlic",
            user=sample_user()
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test the recipe string representation"""
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='Blue Cheese Sauce',
            time_minutes=10,
            price=4.50
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_filename_uuid(self, mock_uuid):
        """Test image is saved in correct location"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'test-image.jpg')
        exp_path = f"uploads/recipe/{uuid}.jpg"

        self.assertEqual(file_path, exp_path)