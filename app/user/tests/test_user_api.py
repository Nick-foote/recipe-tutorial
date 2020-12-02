from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """shortens the create user code by losing 'get_user_model().objects'
    """
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Tests users Public API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user valid payload is successful"""
        payload = {'email': 'test@gmail.com',
                   'password': 'pass123',
                   'name': 'Test Name',
                   }
        resp = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(**resp.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', resp.data)

    def test_user_exists(self):
        """Test user is not created fails, if already exists"""
        payload = {'email': 'test@gmail.com',
                   'password': 'pass123',
                   'name': 'Test Name',
                   }
        create_user(**payload)
        resp = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test password fails if less than 6 characters, and user is not created."""
        payload = {'email': 'test@gmail.com',
                   'password': '12345',
                   'name': 'Test Name',
                   }
        resp = self.client.post(CREATE_USER_URL, payload)

        self.assertTrue(resp.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()

        self.assertFalse(user_exists)

    ###
    def test_create_token_for_user(self):
        """Test a token is created for a user"""
        payload = {'email': 'testtoken@gmail.com',
                   'password': 'pass123',
                   'name': 'Test Token User'
                   }
        create_user(**payload)
        resp = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test token is not created with invalid password"""
        create_user(email='test@gmail.com',
                    password='pass123',
                    name='Test Name',
                    )
        payload = {'email': 'test@gmail.com',
                   'password': 'Incorrect',
                   }
        resp = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    ####
    def test_create_token_no_user(self):
        """Test a token is not created when a user doesn not exist"""
        payload = {'email': 'test@gmail.com',
                   'password': 'pass123',
                   'name': 'Test Name',
                   }
        resp = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


    def test_create_token_no_password(self):
        """Test a token is not created when password is empty"""
        create_user(email='test@gmail.com',
                    password='12345',
                    name='Test Name',
                    )
        payload = {'email': 'test@gmail.com',
                   'password': '',
                   }
        resp = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorised(self):
        """Test authorisation is required for users"""
        resp = self.client.get(ME_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITest(TestCase):
    """Tests API requests that require user authentication"""

    def setUp(self):
        self.user = create_user(
            email='test@gmail.com',
            password='pass123',
            name='Test Name',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


    def test_retrieve_profile_success(self):
        """Retrieving profile for logged in user"""
        resp = self.client.get(ME_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {
            'email': 'test@gmail.com',
            'name': 'Test Name',
        })

    def test_post_me_not_allowed(self):
        """Test you cannot send a POST request to user/me"""
        resp = self.client.post(ME_URL, {})

        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile_successful(self):
        """Test to update a users profile works"""
        payload = dict(
            password='newpassword',
            name='New Name',
        )
        resp = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)



## response.data returns:
# {'email': 'test@gmail.com', 'name': 'New Name'}