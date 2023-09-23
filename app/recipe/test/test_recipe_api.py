"""
recipe api
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
    RecipeSerializers,
    RecipeDetailSerializers,
)

RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """create and return recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])



def create_recipe(user, **params):
    """create and reutrn sample api"""
    defaults = {
        'title':'sample recipe title',
        'time_minutes':22,
        'price':Decimal('5.25'),
        'description':'sample description',
        'link':'http://example.com/recipe.pdf'

    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe



def create_user(**params):
    """create and return a new user"""
    return get_user_model().objects.create_user(**params)



class PublicRecipeApiTests(TestCase):
    """test unautheticated api request"""

    def setUp(self):
        self.client=APIClient()

    def test_auth_required(self):
        """test auth is required to call API"""

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):
    """test authenticated api request"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password ='testpass123', )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """retrieving authenticated user"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)


        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializers(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """test lsit of recipe is limmited tp authenticated user"""
        other_user =  create_user(email='other@example.com', password ='test123', )
        create_recipe(user = other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializers(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_get_recipe_detail(self):
        """Test get recipe detail view"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializers(recipe)
        self.assertEqual(res.data, serializer.data)


    def test_create_recipe(self):
        """test create a recipe"""
        payload = {
            'title': 'sample recipe',
            'time_minutes':30,
            'price':Decimal('5.34'),

        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)


    def test_partial_update(self):
        """test partial update of the recipe"""
        original_link= 'http://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title = 'sample recipe',
            link = original_link,
        )

        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)


    def test_full_update(self):
        """test full update"""
        recipe= create_recipe(
            user=self.user,
            title = 'sample recipe title',
            link='http://example.com/recipe.pdf',
            description='Sample recipe description',
        )

        payload = {
            'title':'New reciope Title',
            'link': 'http://example.com/recipe.pdf',
            'description':'new recipe description',
            'time_minutes':10,
            'price':Decimal('2.50'),
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)


    def test_update_user_returns_error(self):
        """test changing recipe user reuslt in  error"""
        new_user = create_user(email='user2@example.com', password='test123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)


    def test_delete_recipe(self):
        """test deleting a recipe"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())


    def test_other_user_recipe_error(self):
        """Test error when updating other user's recipe"""
        other_user = create_user(email='other@example.com', password='test123')
        recipe = create_recipe(user=other_user)

        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        recipe.refresh_from_db()
        self.assertNotEqual(recipe.title, payload['title'])
        self.assertNotEqual(recipe.user, self.user)

    def test_delete_other_user_recipe_error(self):
        """Test error when trying to delete another user's recipe"""
        new_user = create_user(email='other@example.com', password='test123')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

