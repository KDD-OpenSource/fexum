from rest_framework.test import APITestCase
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, \
    SampleFactory, DatasetFactory, ExperimentFactory, RelevancyFactory, RedundancyFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT, \
    HTTP_400_BAD_REQUEST
from features.serializers import FeatureSerializer, BinSerializer, SliceSerializer, \
    SampleSerializer, DatasetSerializer, ExperimentSerializer, ExperimentTargetSerializer, \
    RelevancySerializer, RedundancySerializer
from unittest.mock import patch
from features.models import Experiment, Dataset
from django.contrib.auth import get_user_model
import os
import zipfile


class TestExperimentListView(APITestCase):
    def test_retrieve_experiment_list(self):
        experiment = ExperimentFactory()

        url = reverse('experiment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        json_data = response.json()
        data = ExperimentSerializer(instance=experiment).data
        first_obj = json_data.pop(0)
        self.assertEqual(len(json_data), 0)
        self.assertEqual(first_obj.pop('id'), str(data['id']))
        self.assertEqual(first_obj.pop('dataset'), str(data['dataset']))
        self.assertEqual(first_obj.pop('target'), str(data['target']))

    def test_create_new_experiment(self):
        dataset = DatasetFactory()

        data = {'dataset': dataset.id}
        url = reverse('experiment-list')
        response = self.client.post(url, data=data)

        experiment = Experiment.objects.first()

        data = ExperimentSerializer(instance=experiment).data
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {'id': str(data['id']), 'dataset': str(data['dataset']),
                                           'target': data['target']})

        # Test if creation worked
        self.assertEqual(experiment.dataset, dataset)
        self.assertIsNone(experiment.target)
        self.assertEqual(experiment.user, get_user_model().objects.first())

    def test_create_new_experiment_dataset_missing(self):
        data = {'dataset': '079a60fc-c3b1-48ee-8bb6-ba19f061e9e0'}
        url = reverse('experiment-list')
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'dataset': [
            'Invalid pk "079a60fc-c3b1-48ee-8bb6-ba19f061e9e0" - object does not exist.']})


class TestExperimentDetailView(APITestCase):
    def test_retrieve_experiment_detail(self):
        experiment = ExperimentFactory()

        url = reverse('experiment-detail', args=[experiment.id])
        response = self.client.get(url)

        data = ExperimentSerializer(instance=experiment).data
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {'id': str(data['id']), 'target': str(data['target']),
                                           'dataset': str(data['dataset'])})

    def test_retrieve_experiment_detail_not_found(self):
        url = reverse('experiment-detail', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestTargetDetailView(APITestCase):
    def test_delete_target(self):
        experiment = ExperimentFactory()

        self.assertIsNotNone(experiment.target)

        url = reverse('experiment-targets-detail', args=[experiment.id])
        response = self.client.delete(url)

        experiment = Experiment.objects.get(id=experiment.id)

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')
        self.assertIsNone(experiment.target)

    def test_delete_target_not_found(self):
        url = reverse('experiment-targets-detail', args=['1c6f46c4-e2d6-4378-8dc4-7417cca743da'])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_select_target(self):
        experiment = ExperimentFactory(target=None)
        target = FeatureFactory(dataset=experiment.dataset)

        self.assertIsNone(experiment.target)
        self.assertEqual(experiment.dataset, target.dataset)

        url = reverse('experiment-targets-detail', args=[experiment.id])
        with patch('features.views.calculate_rar.delay') as calculate_rar:
            response = self.client.put(url, data={'target': target.id}, format='json')

            self.assertEqual(response.status_code, HTTP_200_OK)

            experiment = Experiment.objects.get(id=experiment.id)
            data = ExperimentTargetSerializer(instance=experiment).data
            self.assertEqual(experiment.target, target)
            self.assertEqual(response.json(), {'target': str(data['target'])})
            calculate_rar.assert_called_once_with(target_id=target.id)

    def test_select_target_feature_not_found(self):
        target = FeatureFactory()

        url = reverse('experiment-targets-detail', args=['5781ca8a-3c7d-46b4-897e-90d80e938258'])
        response = self.client.put(url, data={'target': target.id}, format='json')

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_select_feature_should_not_accept_different_datasets(self):
        experiment = ExperimentFactory(target=None)
        target = FeatureFactory()

        self.assertIsNone(experiment.target)
        self.assertNotEqual(experiment.dataset, target.dataset)

        url = reverse('experiment-targets-detail', args=[experiment.id])
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
    file_name = 'features/tests/test_file.csv'
    url = reverse('dataset-upload')
    zip_file_name = 'archive.zip'

    def test_upload_dataset(self):
        with zipfile.ZipFile(self.zip_file_name, 'w') as zip_file:
            zip_file.write(self.file_name)

        with patch('features.views.initialize_from_dataset.apply_async') as initialize_from_dataset_mock:
            with open(self.zip_file_name, 'rb') as file_data:
                response = self.client.put(self.url, {'file': file_data}, format='multipart')

            dataset = Dataset.objects.first()
            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.json(), DatasetSerializer(instance=dataset).data)
            self.assertEqual(dataset.name, self.file_name)
            with open(self.file_name, 'rb') as file_data:
                self.assertEqual(dataset.content.read(), file_data.read())
            initialize_from_dataset_mock.assert_called_once_with(args=[dataset.id], queue=str(dataset.id))

    def test_upload_dataset_no_zip_file(self):
        with open(self.file_name) as file_data:
            response = self.client.put(self.url, {'file': file_data}, format='multipart')

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'detail': 'Uploaded file is not a zip file.'})

    def test_upload_dataset_no_csv_in_zip(self):
        empty_zip_data = b'PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
                         b'\x00\x00\x00\x00\x00\x00\x00'
        with open(self.zip_file_name, 'w+b') as zip_file:
            zip_file.write(empty_zip_data)

        with open(self.zip_file_name, 'rb') as zip_file:
            response = self.client.put(self.url, {'file': zip_file}, format='multipart')

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'detail': 'No CSV file found in ZIP archive.'})

    def tearDown(self):
        # Remove that shitty file
        if os.path.isfile(self.zip_file_name):
            os.remove(self.zip_file_name)
            self.assertFalse(os.path.isfile(self.zip_file_name))


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
        self.assertEqual(first_obj.pop('is_categorical'), data['is_categorical'])
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

        url = reverse('target-feature-slices',
                      args=[fslice.relevancy_result.target.id, fslice.relevancy_result.feature.id])
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
        self.assertEqual(len(first_obj), 0)

    def test_retrieve_slices_feature_not_found(self):
        target = FeatureFactory()

        url = reverse('target-feature-slices',
                      args=[target.id, '7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_retrieve_slices_target_not_found(self):
        url = reverse('target-feature-slices', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e',
                                                      '8a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestFeatureRelevancyResultsView(APITestCase):
    def test_retrieve_relevancy_results(self):
        relevancy = RelevancyFactory()

        url = reverse('target-feature-relevancy_results', args=[relevancy.target.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        data = RelevancySerializer(instance=relevancy).data
        json_data = response.json()
        first_obj = json_data.pop(0)
        self.assertEqual(len(json_data), 0)
        self.assertEqual(first_obj.pop('id'), str(data['id']))
        self.assertEqual(first_obj.pop('feature'), str(data['feature']))
        self.assertEqual(first_obj.pop('target'), str(data['target']))
        self.assertAlmostEqual(first_obj.pop('relevancy'), data['relevancy'])
        self.assertEqual(first_obj.pop('rank'), data['rank'])
        self.assertEqual(len(first_obj), 0)

    def test_retrieve_relevancy_results_target_not_found(self):
        url = reverse('target-feature-relevancy_results',
                      args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestFeatureRedundancyResults(APITestCase):
    def test_retrieve_redundancy_results(self):
        first_feature = FeatureFactory()
        second_feature = FeatureFactory(dataset=first_feature.dataset)
        redundancy = RedundancyFactory(first_feature=first_feature,
                                              second_feature=second_feature)
        serializer = RedundancySerializer(instance=redundancy)

        url = reverse('feature-redundancy_results',
                      args=[redundancy.first_feature.dataset.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        response_data = response.json()
        first_obj = response_data.pop(0)
        self.assertEqual(first_obj.pop('id'), str(serializer.data['id']))
        self.assertEqual(first_obj.pop('first_feature'), str(serializer.data['first_feature']))
        self.assertEqual(first_obj.pop('second_feature'), str(serializer.data['second_feature']))
        self.assertAlmostEqual(first_obj.pop('weight'), serializer.data['weight'])
        self.assertAlmostEqual(first_obj.pop('redundancy'), serializer.data['redundancy'])
        self.assertEqual(len(response_data), 0)
        self.assertEqual(len(first_obj), 0)

    def test_retrieve_redundancy_results_dataset_not_found(self):
        url = reverse('feature-redundancy_results', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestFilteredSlicesView(APITestCase):
    def test_retrieve_filtered_slices(self):
        slice1 = SliceFactory()
        SliceFactory()

        url = '{0}?feature__in={1}'.format(
            reverse('target-filtered-slices', args=[slice1.relevancy_result.target.id]),
            slice1.relevancy_result.feature.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['features'][0]['feature'],
                         str(slice1.relevancy_result.feature.id))

    def test_retrieve_filtered_slices_target_not_found(self):
        url = reverse('target-filtered-slices', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestCondiditonalDistributionsView(APITestCase):
    def test_conditional_distributions_target_not_found(self):
        pass

    def test_conditional_distributions_feature_not_found(self):
        pass

    def test_conditional_distributions_missing_data(self):
        pass

    def test_conditional_distributions(self):
        target = FeatureFactory()
        feature = FeatureFactory(dataset=target.dataset)

        data = [{
            'feature': feature.id,
            'from_value': -1,
            'to_value': 1
        }]

        url = reverse('target-condidtional-distributions', args=[target.id])
        with patch('features.views.calculate_conditional_distributions.apply_async',) as task_mock:
            task_mock.get.return_value = []
            response = self.client.post(url, data=data, format='json')
            task_mock.assert_called_once_with(
                target_id=target.id,
                feature_ranges=data,
                queue=target.dataset.id
            )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [])
