from django.test import TestCase
from django.contrib.auth import get_user_model


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

