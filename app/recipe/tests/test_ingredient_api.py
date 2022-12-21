from unicodedata import name
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIANTS_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id])

def create_user(email='ingredient@emxaple.com', password='testpass123'):
    return get_user_model().objects.create_user(email=email, password=password)

class PublicIngredientAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        res = self.client.get(INGREDIANTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class privateIngredientAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
    
    def test_retrive_ingredients(self):
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Vanilla')

        res = self.client.get(INGREDIANTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limit_to_user(self):
        user2 = create_user(email='user2@example.com')
        Ingredient.objects.create(user=user2, name='Salt')
        ingredient = Ingredient.objects.create(user=self.user, name='Papper')

        res = self.client.get(INGREDIANTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_ingredient_update(self):
        ingredient = Ingredient.objects.create(user=self.user, name='Drumstick')
        payload = {'name': 'Tomatoes'}

        res = self.client.patch(detail_url(ingredient.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_ingredient_delete(self):
        ingredient = Ingredient.objects.create(user=self.user, name="Black Papper")
        res = self.client.delete(detail_url(ingredient.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())