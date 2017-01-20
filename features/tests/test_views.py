from rest_framework.test import APITestCase
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, \
    SampleFactory, DatasetFactory, SessionFactory, RarResultFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT, \
    HTTP_400_BAD_REQUEST
from features.serializers import FeatureSerializer, BinSerializer, SliceSerializer, \
    SampleSerializer, DatasetSerializer, SessionSerializer, SessionTargetSerializer, \
    RarResultSerializer
from unittest.mock import patch
from features.models import Session, Dataset
from django.contrib.auth import get_user_model
import os

class TestSessionListView(APITestCase):
    def test_retrieve_session_list(self):
        session = SessionFactory()

        url = reverse('session-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        json_data = response.json()
        data = SessionSerializer(instance=session).data
        first_obj = json_data.pop(0)
        self.assertEqual(len(json_data), 0)
        self.assertEqual(first_obj.pop('id'), str(data['id']))
        self.assertEqual(first_obj.pop('dataset'), str(data['dataset']))
        self.assertEqual(first_obj.pop('target'), str(data['target']))

    def test_create_new_session(self):
        dataset = DatasetFactory()

        data = {'dataset': dataset.id}
        url = reverse('session-list')
        response = self.client.post(url, data=data)

        session = Session.objects.first()

        data = SessionSerializer(instance=session).data
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {'id': str(data['id']), 'dataset': str(data['dataset']),
                                           'target': data['target']})

        # Test if creation worked
        self.assertEqual(session.dataset, dataset)
        self.assertIsNone(session.target)
        self.assertEqual(session.user, get_user_model().objects.first())

    def test_create_new_session_dataset_missing(self):
        data = {'dataset': '079a60fc-c3b1-48ee-8bb6-ba19f061e9e0'}
        url = reverse('session-list')
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'dataset': [
            'Invalid pk "079a60fc-c3b1-48ee-8bb6-ba19f061e9e0" - object does not exist.']})


class TestSessionDetailView(APITestCase):
    def test_retrieve_session_detail(self):
        session = SessionFactory()

        url = reverse('session-detail', args=[session.id])
        response = self.client.get(url)

        data = SessionSerializer(instance=session).data
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {'id': str(data['id']), 'target': str(data['target']),
                                           'dataset': str(data['dataset'])})

    def test_retrieve_session_detail_not_found(self):
        url = reverse('session-detail', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestTargetDetailView(APITestCase):
    def test_delete_target(self):
        session = SessionFactory()

        self.assertIsNotNone(session.target)

        url = reverse('session-targets-detail', args=[session.id])
        response = self.client.delete(url)

        session = Session.objects.get(id=session.id)

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')
        self.assertIsNone(session.target)

    def test_delete_target_not_found(self):
        url = reverse('session-targets-detail', args=['1c6f46c4-e2d6-4378-8dc4-7417cca743da'])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_select_target(self):
        session = SessionFactory(target=None)
        target = FeatureFactory(dataset=session.dataset)

        self.assertIsNone(session.target)
        self.assertEqual(session.dataset, target.dataset)

        url = reverse('session-targets-detail', args=[session.id])
        with patch('features.views.calculate_rar.delay') as calculate_rar:
            response = self.client.put(url, data={'target': target.id}, format='json')

            self.assertEqual(response.status_code, HTTP_200_OK)

            session = Session.objects.get(id=session.id)
            data = SessionTargetSerializer(instance=session).data
            self.assertEqual(session.target, target)
            self.assertEqual(response.json(), {'target': str(data['target'])})
            calculate_rar.assert_called_once_with(target_id=target.id)

    def test_select_target_feature_not_found(self):
        target = FeatureFactory()

        url = reverse('session-targets-detail', args=['5781ca8a-3c7d-46b4-897e-90d80e938258'])
        response = self.client.put(url, data={'target': target.id}, format='json')

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_select_feature_should_not_accept_different_datasets(self):
        session = SessionFactory(target=None)
        target = FeatureFactory()

        self.assertIsNone(session.target)
        self.assertNotEqual(session.dataset, target.dataset)

        url = reverse('session-targets-detail', args=[session.id])
        response = self.client.put(url, data={'target': target.id}, format='json')

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'target': ['Target must be from the same dataset.']})


class TestDatasetListView(APITestCase):
    def test_retrieve_all_datasets(self):
        dataset = DatasetFactory()

        url = reverse('dataset-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [DatasetSerializer(instance=dataset).data])


class TestDatasetUploadView(APITestCase):
    def test_upload_dataset(self):
        file_name = 'test_file.csv'

        url = reverse('dataset-upload')
        with patch('features.views.initialize_from_dataset.delay') as initialize_from_dataset_mock:
            with open(file_name) as file_data:
                response = self.client.put(url, {'file': file_data}, format='multipart')

            dataset = Dataset.objects.first()
            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.json(), DatasetSerializer(instance=dataset).data)
            self.assertEqual(dataset.name, file_name)
            with open(file_name, 'rb') as file_data:
                self.assertEqual(dataset.content.read(), file_data.read())
            initialize_from_dataset_mock.assert_called_once_with(dataset_id=dataset.id)


class TestFeatureListView(APITestCase):
    def test_retrieve_feature_list(self):
        feature = FeatureFactory()

        url = reverse('dataset-features-list', args=[feature.dataset.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        json_data = response.json()
        data = FeatureSerializer(instance=feature).data
        self.assertEqual(len(json_data), 1)
        first_obj = json_data.pop(0)
        self.assertAlmostEqual(first_obj.pop('min'), data['min'])
        self.assertAlmostEqual(first_obj.pop('mean'), data['mean'])
        self.assertAlmostEqual(first_obj.pop('max'),  data['max'])
        self.assertAlmostEqual(first_obj.pop('variance'),  data['variance'])
        self.assertEqual(first_obj.pop('id'), data['id'])
        self.assertEqual(first_obj.pop('name'), data['name'])
        self.assertEqual(len(first_obj), 0)

    def test_retrieve_feature_list_dataset_not_found(self):
        url = reverse('dataset-features-list', args=['5781ca8a-3c7d-46b4-897e-90d80e938258'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


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
        session = SessionFactory(target=fslice.rar_result.target)

        url = reverse('session-feature-slices',
                      args=[session.id, fslice.rar_result.feature.id])
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

    def test_retrieve_slices_feature_not_found(self):
        session = SessionFactory()

        url = reverse('session-feature-slices',
                      args=[session.id, '7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_retrieve_slices_session_not_found(self):
        url = reverse('session-feature-slices', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e',
                                                      '8a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestFeatureRarResultsView(APITestCase):
    def test_retrieve_rar_results(self):
        rar_result = RarResultFactory()
        session = SessionFactory(target=rar_result.target, dataset=rar_result.feature.dataset)

        url = reverse('session-feature-rar_results', args=[session.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        data = RarResultSerializer(instance=rar_result).data
        json_data = response.json()
        first_obj = json_data.pop(0)
        self.assertEqual(len(json_data), 0)
        self.assertEqual(first_obj.pop('id'), str(data['id']))
        self.assertEqual(first_obj.pop('feature'), str(data['feature']))
        self.assertAlmostEqual(first_obj.pop('relevancy'), data['relevancy'])
        self.assertAlmostEqual(first_obj.pop('redundancy'), data['redundancy'])
        self.assertEqual(first_obj.pop('rank'), data['rank'])
        self.assertEqual(len(first_obj), 0)

    def test_retrieve_rar_session_not_found(self):
        url = reverse('session-feature-rar_results', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

