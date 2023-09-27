"""
recipe api
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
)

from recipe.serializers import (
    RecipeSerializers,
    RecipeDetailSerializers,
    Ingredient,
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


    def test_create_recipe_with_new_tags(self):
        """test creating a recipe with new tag"""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes':30,
            'price':Decimal('2.50'),
            'tags':[{'name':'Thai'}, {'name':'Dinner'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists=recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_recipe_with_existing_tags(self):
        """test creating a recipe with existing tag"""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes':60,
            'price':Decimal('4.50'),
            'tags':[{'name':'Indian'}, {'name':'Breakfast'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists=recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)



    def test_create_tag_on_update(self):
        """Test creating a tag on updating a recipe"""
        Tag.objects.create(user=self.user, name='Lunch')
        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        new_tag = Tag.objects.get(name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())



    def test_update_recipe_assign_tag(self):
        """Test asssigning an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags':[{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """test clearing a recipe tags"""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_new_ingredient(self):
        """Test creating a new ingredient"""
        payload = {
            'title':'Cauliflower Tacos',
            'time_minutes':60,
            'price':Decimal('4.30'),
            'ingredients':[{'name': 'Cauliflower'}, {'name':'salt'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes= Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists=recipe.ingredients.filter(
                name=ingredient['name'],
                user =self.user,
            ).exists()
            self.assertTrue(recipes)


    def test_create_recipe_with_existing_ingredient(self):
        """creating an ingredient with an existing ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Lemon')
        payload = {
            'title':'Cauliflower Tacos',
            'time_minutes':60,
            'price':Decimal('4.30'),
            'ingredients':[{'name': 'Lemon'}, {'name':'Fish Sauce'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes= Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists=recipe.ingredients.filter(
                name=ingredient['name'],
                user =self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_ingredient_on_updata(self):
        """test creating an ingresient when updating a recipe"""
        recipe = create_recipe(user=self.user)
        payload={'ingredients':[{'name': 'Limes'}]}
        url = detail_url(recipe.id)
        res =self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Limes')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Chili')
        recipe.ingredients.add(ingredient2)  # Add ingredient2 to the recipe

        payload = {
            'ingredients': [{'name': 'Chili'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.ingredients.remove(ingredient1)  # Remove ingredient1 from the recipe

        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing all ingredients from a recipe"""
        recipe = create_recipe(user=self.user)
        ingredient1 = Ingredient.objects.create(user=self.user, name='Pepper')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Chili')
        recipe.ingredients.add(ingredient1, ingredient2)
        url = detail_url(recipe.id)
        payload = {'ingredients': []}
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        recipe.ingredients.clear()  # Clear all ingredients from the recipe
        self.assertEqual(recipe.ingredients.count(), 0)
