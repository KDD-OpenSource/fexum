from rest_framework.test import APITestCase
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, TargetFactory, SampleFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT
from features.serializers import FeatureSerializer, BinSerializer, SliceSerializer, TargetSerializer, SampleSerializer
from features.models import Target
from unittest.mock import patch


class TestFeatureListView(APITestCase):
    def test_retrieve_feature_list(self):
        feature = FeatureFactory()

        url = reverse('feature-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [FeatureSerializer(instance=feature).data])


class TestFeatureSamplesView(APITestCase):
    def test_retrieve_samples(self):
        sample = SampleFactory()

        url = reverse('feature-samples', args=[sample.feature.name])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        data = SampleSerializer(instance=sample).data
        json_data = response.json()
        self.assertEqual(len(json_data), 1)
        self.assertAlmostEqual(json_data.pop(0).pop('value'), data['value'])
        self.assertEqual(len(json_data), 0)


class TestFeatureHistogramView(APITestCase):
    def test_retrieve_histogram(self):
        hbin = BinFactory()

        url = reverse('feature-histogram', args=[hbin.feature.name])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        data = BinSerializer(instance=hbin).data
        json_data = response.json()
        self.assertEqual(len(json_data), 1)
        first_obj = json_data.pop(0)
        self.assertEqual(len(json_data), 0)
        self.assertEqual(first_obj.pop('count'), data['count'])
        self.assertAlmostEqual(first_obj.pop('to_value'), data['to_value'])
        self.assertAlmostEqual(first_obj.pop('from_value'), data['from_value'])
        self.assertEqual(len(first_obj), 0)

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
        data = SliceSerializer(instance=fslice).data
        json_data = response.json()
        self.assertEqual(len(json_data), 1)
        first_obj = json_data.pop(0)
        self.assertEqual(len(json_data), 0)
        self.assertEqual(first_obj.pop('conditional_distribution'), data['conditional_distribution'])
        self.assertEqual(first_obj.pop('marginal_distribution'), data['marginal_distribution'])
        self.assertAlmostEqual(first_obj.pop('to_value'), data['to_value'])
        self.assertAlmostEqual(first_obj.pop('from_value'), data['from_value'])
        self.assertAlmostEqual(first_obj.pop('score'), data['score'])
        self.assertEqual(len(first_obj), 0)

    def test_retrieve_slices_not_found(self):
        url = reverse('feature-slices', args=['Some_feature_name'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestTargetDetailView(APITestCase):
    def test_retrieve_target(self):
        target = TargetFactory()

        url = reverse('target-detail')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), TargetSerializer(instance=target).data)

    def test_retrieve_target_no_target(self):
        url = reverse('target-detail')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {'feature': None})

    def test_delete_target(self):
        TargetFactory()

        url = reverse('target-detail')
        response = self.client.delete(url)

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')
        self.assertEqual(Target.objects.count(), 0)

    def test_delete_target_not_found(self):
        url = reverse('target-detail')
        response = self.client.delete(url)

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

    def test_select_target(self):
        feature = FeatureFactory()
        self.assertEqual(Target.objects.count(), 0)

        url = reverse('target-detail')
        with patch('features.views.calculate_rar.delay') as calculate_rar:
            response = self.client.put(url, data={'feature': {'name': feature.name}}, format='json')

            self.assertEqual(Target.objects.count(), 1)
            self.assertEqual(Target.objects.get().feature, feature)
            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.json(), TargetSerializer(instance=Target.objects.get()).data)
            calculate_rar.assert_called_once_with('')  # TODO: Replace with actual path

    def test_select_target_feature_not_found(self):
        url = reverse('target-detail')
        response = self.client.put(url, data={'feature': {'name': 'foobar'}}, format='json')

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_select_target_already_selected(self):
        feature = FeatureFactory()
        target = TargetFactory()
        self.assertEqual(Target.objects.count(), 1)

        url = reverse('target-detail')
        with patch('features.views.calculate_rar.delay') as calculate_rar:
            response = self.client.put(url, data={'feature': {'name': feature.name}}, format='json')

            self.assertEqual(Target.objects.count(), 1)
            self.assertEqual(Target.objects.get().feature, feature)
            self.assertNotEqual(Target.objects.get().feature, target.feature)
            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.json(), TargetSerializer(instance=Target.objects.get()).data)
            calculate_rar.assert_called_once_with('')
