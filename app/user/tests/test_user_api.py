from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKE_URL = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params):
    user = get_user_model().objects.create_user(**params)
    return user

class PublicUserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_successflly(self):
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User Name',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
    
    def test_user_with_email_exists_error(self):
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User Name',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_too_short_error(self):
        payload = {
            'email': 'test@example.com',
            'password': 'pw',
            'name': 'Test User Name',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)
    
    def test_create_token(self):
        user_details = {
            'email': 'test@example.com',
            'password': 'pwtest123',
            'name': 'Test User Name',
        }
        create_user(**user_details)
        payload ={
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKE_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code , status.HTTP_200_OK)

    def test_create_token_with_bad_credential(self):
        create_user(email='test@example.com', password='goodpass')
        payload = {
            'email': 'test@example.com', 'password': 'badpass'
        }
        res = self.client.post(TOKE_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_with_blank_password(self):
        create_user(email='test@example.com', password='goodpass')
        payload = {
            'email': 'test@example.com', 'password': ''
        }
        res = self.client.post(TOKE_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrive_user_unauthorized(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password="password123456",
            name="Test Name",
        )
        self.client = APIClient()
        self.client.force_authentication(user=self.user)
    def test_retrieve_profile_successfully(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {'name': 'Updated Name', 'password': 'updatedpassword'}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)