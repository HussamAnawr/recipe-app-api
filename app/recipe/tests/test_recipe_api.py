from decimal import Decimal
from core.models import Recipe, Tag, Ingredient
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

import os
import tempfile
from PIL import Image

from rest_framework import status
from rest_framework.test import APIClient
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPE_URL = reverse('recipe:recipe-list')

def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def deatil_url(detail_id):
    """Getting the recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[detail_id])

def create_recipe(user, **params):
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.23'),
        'description': 'Sample recipe description',
        'link': 'http://example.com/recipe.pdf'
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)

def create_user(**params):
    return get_user_model().objects.create_user(**params)



class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test1@example.com',
            'testpass123',
        )
        self.client.force_authenticate(self.user)
    
    def test_retrive_recipes(self):
        create_recipe(self.user)
        create_recipe(self.user)
        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        other_user = get_user_model().objects.create_user('test2@example.com', 'testpass123456')
        create_recipe(other_user)
        create_recipe(self.user)
        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        recipe = create_recipe(self.user)
        res = self.client.get(deatil_url(recipe.id))
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        payload = {
            'title': 'Sample Title', 
            'time_minutes': 30, 
            'price': Decimal('5.99'),
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(self.user, recipe.user)
        
    def test_partial_update(self):
        orginal_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=orginal_link,
        )
        payload = {
            'title': 'New Recipe Title'
        }
        res = self.client.patch(deatil_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, orginal_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='https://example.com/recipe.pdf',
            description='Sample recipe description',
        )
        payload = {
            'title': 'New recipe title',
            'link': 'https://example.com/new-recipe.pdf',
            'description': 'New recipe description',
            'time_minutes': 10,
            'price': Decimal('2.5')
        }
        res = self.client.put(deatil_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k , v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)
    
    def test_create_recipe_with_new_tag(self):
        payload = {
            'title': 'New recipe',
            'link': 'https://example.com/new-recipe.pdf',
            'time_minutes': 10,
            'price': Decimal('2.5'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exist = recipe.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exist)
    
    def test_create_recipe_with_existing_tag(self):
        tag_indian = Tag.objects.create(name='Indian', user=self.user)
        payload = {
            'title': 'New recipe',
            'link': 'https://example.com/new-recipe.pdf',
            'time_minutes': 10,
            'price': Decimal('2.5'),
            'tags': [{'name': 'Indian'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exist = recipe.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exist)
    
    def test_create_tag_on_update(self):
        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [{'name': 'Lunch'}],
        }
        url = deatil_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        breakfast_tag = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(breakfast_tag)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        res = self.client.patch(deatil_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(breakfast_tag, recipe.tags.all())

    def test_clear_recipe_tags(self):
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = deatil_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
    
    def test_create_recipe_with_new_ingredient(self):
        payload = {
            'title': 'Cauliflower Tacos', 
            'time_minutes': 60, 
            'price': Decimal('2.5'),
            'ingredients': [{'name': 'Cauliflower'}, {'name': 'Salt'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes[0].ingredients.count(), 2)
        self.assertEqual(recipes.count(), 1)
        for ingerdient in payload['ingredients']:
            exiest = recipes[0].ingredients.filter(name=ingerdient['name'], user=self.user).exists()
            self.assertTrue(exiest)

    def test_create_recipe_with_old_ingredient(self):
        ingerdient = Ingredient.objects.create(name='Lemon', user=self.user)
        payload = {
            'title': 'Some Salat', 
            'time_minutes': 60, 
            'price': Decimal('2.5'),
            'ingredients': [{'name': 'Lemon'}, {'name': 'Apple'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertEqual(recipes.count(), 1)
        for ingerdient in payload['ingredients']:
            exiest = recipe.ingredients.filter(name=ingerdient['name'], user=self.user).exists()
            self.assertTrue(exiest)

    def test_create_ingredient_on_update(self):
        recipe = create_recipe(user=self.user)
        payload = {'ingredients': [{'name': 'Limes'}]}
        res = self.client.patch(deatil_url(recipe.id), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Limes')
        recipe.refresh_from_db()
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assgin_ingredient(self):
        ingredient1 = Ingredient.objects.create(user=self.user, name='Pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Chill')
        payload = {'ingredients': [{'name': 'Chill'}]}
        res = self.client.patch(deatil_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        ingredient1 = Ingredient.objects.create(user=self.user, name='Pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        payload = {'ingredients': []}
        res = self.client.patch(deatil_url(recipe.id), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


class RecipeImageAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='exampleemail@exampel.com', password='examplepassword1234')
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')
        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'nothing_here'}
        res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

