from rest_framework.test import APITestCase
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, TargetFactory, SampleFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT
from features.serializers import FeatureSerializer, BinSerializer, SliceSerializer, TargetSerializer, SampleSerializer
from features.models import Target


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
        self.assertEqual(Target.objects.count(), 0)

        url = reverse('target-select', args=[feature.name])
        response = self.client.post(url)

        self.assertEqual(Target.objects.count(), 1)
        self.assertEqual(Target.objects.get().feature, feature)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), TargetSerializer(instance=Target.objects.get()).data)

    def test_select_target_feature_not_found(self):
        url = reverse('target-select', args=['Some_feature_name'])
        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(),  {'detail': 'Not found.'})

    def test_select_target_already_selected(self):
        pass


class TestFeatureSamplesView(APITestCase):
    def test_retrieve_samples(self):
        sample = SampleFactory()

        url = reverse('feature-samples', args=[sample.feature.name])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        data = SampleSerializer(instance=sample).data
        self.assertEqual(response.json(), [{'value': float(data['value'])}])


class TestFeatureHistogramView(APITestCase):
    def test_retrieve_histogram(self):
        hbin = BinFactory()

        url = reverse('feature-histogram', args=[hbin.histogram.feature.name])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        data = BinSerializer(instance=hbin).data
        self.assertEqual(response.json(), [
            {'count': data['count'], 'to_value': float(data['to_value']),
             'from_value': float(data['from_value'])}])

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
        # Convert decimal to float for comparing serialization
        data['to_value'] = float(data['to_value'])
        data['from_value'] = float(data['from_value'])
        self.assertEqual(response.json(), [data])

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

    def test_retrieve_target_not_found(self):
        url = reverse('target-detail')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

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

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})
