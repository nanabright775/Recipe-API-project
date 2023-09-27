"""
test for the ingredient models
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')

def detail_url(ingredients_id):
    """return ingredients detail url"""
    return reverse('recipe:ingredient-detail', args=[ingredients_id])

def create_user(email='user@example.com', password='testpass123'):
    """create and retrun a user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientApiTest(TestCase):
    """Test unauthenticated API request"""
    def setUp(self):
        self.client = APIClient()


    def test_auth_required(self):
        """test auth is required for retrieving an ingredient"""

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """test for an unauthenticated API request"""
    def setUp(self):
        self.user=create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)


    def test_retrieve_ingredient(self):
        """test to retrieve a list ingredient"""
        Ingredient.objects.create(user=self.user, name='kale')
        Ingredient.objects.create(user=self.user, name='Vanilla')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_ingredients_limited_to_user(self):
        """test list of ingredient is limmited an authenticated user"""

        user2=create_user(email='user2@example.com')
        Ingredient.objects.create(user=user2, name='Salt')
        ingredient=Ingredient.objects.create(user=self.user, name='Pepper')

        res = self.client.get(INGREDIENT_URL)


        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)




    def test_update_ingredient(self):
        """test updating an ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Cilatro')
        payload = {'name': 'Cilantro updated'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """test deleting an ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Cilantro')
        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
      #  ingredients=Ingredient.objects.filter(user=self.user)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    

