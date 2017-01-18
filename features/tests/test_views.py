from rest_framework.test import APITestCase
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, \
    SampleFactory, DatasetFactory, SessionFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT, \
    HTTP_400_BAD_REQUEST
from features.serializers import FeatureSerializer, BinSerializer, SliceSerializer, \
    SampleSerializer, DatasetSerializer, SessionSerializer, SessionTargetSerializer
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

            session = Session.objects.get(id=session.id)
            data = SessionTargetSerializer(instance=session).data

            self.assertEqual(session.target, target)
            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.json(), {'target': str(data['target'])})
            calculate_rar.assert_called_once_with(dataset_id=session.dataset.id)

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
        self.assertEqual(response.json(), {})


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


class TestFeatureListView(APITestCase):
    def test_retrieve_feature_list(self):
        feature = FeatureFactory()

        url = reverse('dataset-features-list', args=[feature.dataset.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [FeatureSerializer(instance=feature).data])

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

    def test_retrieve_slices_feature_not_found(self):
        url = reverse('feature-slices', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_retrieve_slices_session_not_found(self):
        url = reverse('feature-slices', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestFeatureRarResultsView(APITestCase):
    def test_retrieve_rar_results(self):
        pass

    def test_retrieve_rar_session_not_found(self):
        pass
