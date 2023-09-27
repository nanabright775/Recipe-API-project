"""Test for tags API"""


from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer



TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    """create and return a tag detail url"""
    return reverse('recipe:tag-detail', args=(tag_id,))


def create_user(email='user@example.com', password = 'testpass123'):
    """create and return a user"""
    return get_user_model().objects.create_user(email=email,password=password)


class PublicTagsApi(TestCase):
    """test unauthenticated API request"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """test auth is required for retrieving tags"""

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PivateTagApiTest(TestCase):
    """Test authorised API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieves_tags(self):
        """Test for retrieving tags for an authorised user."""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_tag_limited_to_user(self):
        """Test list of tags is limitted to authenticated user"""

        user2 = create_user(email='user2@example.com')
        Tag.objects.create(user = user2, name = 'Fruity')
        tag=Tag.objects.create(user=self.user, name='comfort food')

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)



    def test_update_tag(self):
        """test updating a tag"""
        tag = Tag.objects.create(user=self.user, name='After Dinner')

        payload = {'name': 'Desert'}

        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()

        self.assertEqual(tag.name, payload['name'])


    def test_delete_tag(self):
        """Test deleting a tag"""
        tag = Tag.objects.create(user=self.user, name='Break Fast')
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())




