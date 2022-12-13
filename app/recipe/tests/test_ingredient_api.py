from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIANTS_URL = reverse('recipe:ingredient-list')

def create_user(email='ingredient@emxaple.com', password='testpass123'):
    return get_user_model().objects.create_user(email=email, password=password)

class PublicIngredientAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        res = self.client.get(INGREDIANTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class privateIngredientAPITest(TestCase):
    pass