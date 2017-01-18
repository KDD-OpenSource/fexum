from rest_framework.test import APITestCase
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, \
    SampleFactory, DatasetFactory, SessionFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT
from features.serializers import FeatureSerializer, BinSerializer, SliceSerializer, \
    SampleSerializer, DatasetSerializer, SessionSerializer
from unittest.mock import patch
from features.models import Session, Dataset
from django.contrib.auth import get_user_model


class TestSessionListView(APITestCase):
    def test_retrieve_session_list(self):
        session = SessionFactory()

        url = reverse('session-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [SessionSerializer(instance=session).data])

    def test_create_new_session(self):
        dataset = DatasetFactory()

        data = {'dataset': dataset.id}
        url = reverse('session-list')
        response = self.client.post(url, data=data)

        session = Session.objects.first()

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), SessionSerializer(instance=session).data)

        # Test if creation worked
        self.assertEqual(session.dataset, dataset)
        self.assertIsNone(session.target)
        self.assertEqual(session.user, get_user_model().objects.first())

    def test_create_new_session_dataset_missing(self):
        pass


class TestSessionDetailView(APITestCase):
    def test_retrieve_session_detail(self):
        session = SessionFactory()

        url = reverse('session-detail', args=[session.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), SessionSerializer(instance=session).data)

    def test_retrieve_session_detail_not_found(self):
        url = reverse('session-detail', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestFeatureListView(APITestCase):
    def test_retrieve_feature_list(self):
        feature = FeatureFactory()

        url = reverse('dataset-features-list', args=[feature.dataset.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [FeatureSerializer(instance=feature).data])


class TestFeatureSamplesView(APITestCase):
    def test_retrieve_samples(self):
        sample = SampleFactory()

        url = reverse('feature-samples', args=[sample.feature.id])
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

        url = reverse('feature-histogram', args=[hbin.feature.id])
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
        url = reverse('feature-histogram', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestFeatureSlicesView(APITestCase):
    def test_retrieve_slices(self):
        fslice = SliceFactory()

        url = reverse('feature-slices', args=[fslice.rar_result.feature.id])
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
        self.assertAlmostEqual(first_obj.pop('deviation'), data['deviation'])
        self.assertAlmostEqual(first_obj.pop('frequency'), data['frequency'])
        self.assertAlmostEqual(first_obj.pop('significance'), data['significance'])
        self.assertEqual(len(first_obj), 0)

    def test_retrieve_slices_not_found(self):
        url = reverse('feature-slices', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
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
        with patch('features.views.calculate_rar.delay') as calculate_rar_mock:
            response = self.client.put(url, data={'feature': {'name': feature.name}}, format='json')

            self.assertEqual(Target.objects.count(), 1)
            self.assertEqual(Target.objects.get().feature, feature)
            self.assertNotEqual(Target.objects.get().feature, target.feature)
            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.json(), TargetSerializer(instance=Target.objects.get()).data)
            calculate_rar_mock.assert_called_once_with('')


class TestDatasetListView(APITestCase):
    def test_retrieve_all_datasets(self):
        dataset = DatasetFactory()

        url = reverse('dataset-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [DatasetSerializer(instance=dataset).data])


class TestDatasetUploadView(APITestCase):
    def test_upload_dataset(self):
        dataset_name = 'test.csv'

        url = reverse('dataset-upload', args=[dataset_name])
        with patch('features.views.initialize_from_dataset.delay') as initialize_from_dataset_mock:
            with open('test_file.csv') as file_data:
                response = self.client.post(url, {'file': file_data})

            dataset = Dataset.objects.first()
            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.json(), DatasetSerializer(instance=dataset).data)
            self.assertEqual(dataset.name, dataset_name)
            self.assertEqual(dataset.content.open.read(), file_data)
            initialize_from_dataset_mock.assert_called_once_with(dataset_id=dataset.id)
