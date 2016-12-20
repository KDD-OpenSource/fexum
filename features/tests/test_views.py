from rest_framework.test import APITestCase
from features.tests.factories import FeatureFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK
from features.serializers import FeatureSerializer


class TestFeatureListView(APITestCase):
    def test_retrieve_feature_list(self):
        feature = FeatureFactory()

        url = reverse('feature-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [FeatureSerializer(instance=feature).data])
