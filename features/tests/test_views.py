from rest_framework.test import APITestCase
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from features.serializers import FeatureSerializer, BinSerializer, SliceSerializer
from features.models import Feature


class TestFeatureListView(APITestCase):
    def test_retrieve_feature_list(self):
        feature = FeatureFactory()

        url = reverse('feature-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [FeatureSerializer(instance=feature).data])


class TestSelectTargetView(APITestCase):
    def test_select_target(self):
        feature = FeatureFactory()
        self.assertFalse(feature.is_target)

        url = reverse('target-select', args=[feature.name])
        response = self.client.post(url)
        feature.refresh_from_db()

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), FeatureSerializer(instance=feature).data)
        self.assertEqual(Feature.objects.get(is_target=True).name, feature.name)

    def test_select_target_not_found(self):
        url = reverse('target-select', args=['Some_feature_name'])
        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(),  {'detail': 'Not found.'})

    def test_select_target_already_selected(self):
        pass


class TestFeatureSamplesView(APITestCase):
    pass


class TestFeatureHistogramView(APITestCase):
    def test_retrieve_histogram(self):
        hbin = BinFactory()

        url = reverse('feature-histogram', args=[hbin.histogram.feature.name])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [BinSerializer(instance=hbin).data])

    def test_retrieve_histogram_not_found(self):
        url = reverse('feature-histogram', args=['Some_feature_name'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestFeatureSlicesView(APITestCase):
    def test_retrieve_slices(self):
        fslice = SliceFactory()

        url = reverse('feature-slices', args=[fslice.feature.name])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [SliceSerializer(instance=fslice).data])

    def test_retrieve_slices_not_found(self):
        url = reverse('feature-slices', args=['Some_feature_name'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})
