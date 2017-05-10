from rest_framework.test import APITestCase
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, \
    SampleFactory, DatasetFactory, ExperimentFactory, RelevancyFactory, RedundancyFactory, \
    ResultCalculationMapFactory, SpectrogramFactory, CalculationFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT, \
    HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from features.serializers import FeatureSerializer, BinSerializer, \
    SampleSerializer, DatasetSerializer, ExperimentSerializer, ExperimentTargetSerializer, \
    RelevancySerializer, RedundancySerializer, SpectrogramSerializer
from unittest.mock import patch
from features.models import Experiment, Dataset
import os
import zipfile
from users.tests.factories import UserFactory
from uuid import uuid4


class TestExperimentListView(APITestCase):
    def test_retrieve_experiment_list(self):
        experiment = ExperimentFactory()
        ExperimentFactory() # Also just create create a second experiment with a different user

        url = reverse('experiment-list')
        self.client.force_authenticate(experiment.user)
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
        user = UserFactory()

        data = {'dataset': dataset.id}
        url = reverse('experiment-list')
        self.client.force_authenticate(user)
        response = self.client.post(url, data=data)

        experiment = Experiment.objects.first()

        data = ExperimentSerializer(instance=experiment).data
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {'id': str(data['id']), 'dataset': str(data['dataset']),
                                           'target': data['target']})

        # Test if creation worked
        self.assertEqual(experiment.dataset, dataset)
        self.assertIsNone(experiment.target)
        self.assertEqual(experiment.user, user)

    def test_create_new_experiment_dataset_missing(self):
        user = UserFactory()
        data = {'dataset': '079a60fc-c3b1-48ee-8bb6-ba19f061e9e0'}
        url = reverse('experiment-list')

        self.client.force_authenticate(user)
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'dataset': [
            'Invalid pk "079a60fc-c3b1-48ee-8bb6-ba19f061e9e0" - object does not exist.']})

    def test_get_experiment_list_unauthenticated(self):
        url = reverse('experiment-list')
        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestExperimentDetailView(APITestCase):
    def test_retrieve_experiment_detail(self):
        experiment = ExperimentFactory()
        self.client.force_authenticate(experiment.user)

        url = reverse('experiment-detail', args=[experiment.id])
        response = self.client.get(url)

        data = ExperimentSerializer(instance=experiment).data
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {'id': str(data['id']), 'target': str(data['target']),
                                           'dataset': str(data['dataset'])})

    def test_retrieve_experiment_detail_not_found(self):
        user = UserFactory()
        experiment = ExperimentFactory()

        self.assertNotEqual(user, experiment.user)

        self.client.force_authenticate(user)
        url = reverse('experiment-detail', args=[experiment.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_get_experiment_unauthenticated(self):
        url = reverse('experiment-detail', args=['079a60fc-c3b1-48ee-8bb6-ba19f061e9e0'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestTargetDetailView(APITestCase):
    def test_delete_target(self):
        experiment = ExperimentFactory()
        self.client.force_authenticate(experiment.user)

        self.assertIsNotNone(experiment.target)

        url = reverse('experiment-targets-detail', args=[experiment.id])
        response = self.client.delete(url)

        experiment = Experiment.objects.get(id=experiment.id)

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')
        self.assertIsNone(experiment.target)

    def test_delete_target_not_found(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        experiment = ExperimentFactory()
        self.assertNotEqual(user, experiment.user)

        url = reverse('experiment-targets-detail', args=[experiment.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_delete_target_unauthenticated(self):
        url = reverse('experiment-targets-detail', args=['1c6f46c4-e2d6-4378-8dc4-7417cca743da'])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})

    def test_select_target(self):
        experiment = ExperimentFactory(target=None)
        self.client.force_authenticate(experiment.user)

        target = FeatureFactory(dataset=experiment.dataset)
        result_calculation_map = ResultCalculationMapFactory(target=target)
        calculation = CalculationFactory(result_calculation_map=result_calculation_map)


        self.assertIsNone(experiment.target)
        self.assertEqual(experiment.dataset, target.dataset)

        url = reverse('experiment-targets-detail', args=[experiment.id])
        with patch('features.views.calculate_hics.subtask') as calculate_hics, patch('features.views.Calculation.objects.create') as create_calculation:
            create_calculation.return_value = calculation

            response = self.client.put(url, data={'target': target.id}, format='json')

            self.assertEqual(response.status_code, HTTP_200_OK)

            experiment = Experiment.objects.get(id=experiment.id)
            data = ExperimentTargetSerializer(instance=experiment).data
            self.assertEqual(experiment.target, target)
            self.assertEqual(response.json(), {'target': str(data['target'])})
            calculate_hics.assert_called_once_with(immutable=True, kwargs={'calculation': calculation, 'calculate_redundancies': True})
            # TODO: Test chain call

    def test_select_target_feature_not_found(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        target = FeatureFactory()

        url = reverse('experiment-targets-detail', args=['5781ca8a-3c7d-46b4-897e-90d80e938258'])
        response = self.client.put(url, data={'target': target.id}, format='json')

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_select_feature_should_not_accept_different_datasets(self):
        experiment = ExperimentFactory(target=None)
        self.client.force_authenticate(experiment.user)

        target = FeatureFactory()

        self.assertIsNone(experiment.target)
        self.assertNotEqual(experiment.dataset, target.dataset)

        url = reverse('experiment-targets-detail', args=[experiment.id])
        response = self.client.put(url, data={'target': target.id}, format='json')

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'target': ['Target must be from the same dataset.']})

    def test_select_feature_unauthenticated(self):
        url = reverse('experiment-targets-detail', args=['1c6f46c4-e2d6-4378-8dc4-7417cca743da'])
        response = self.client.put(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestDatasetListView(APITestCase):
    def test_retrieve_all_datasets(self):
        user = UserFactory()

        dataset = DatasetFactory()

        url = reverse('dataset-list')
        self.client.force_authenticate(user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [DatasetSerializer(instance=dataset).data])

    def test_retrieve_all_datasets_unauthenticated(self):
        url = reverse('dataset-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestDatasetUploadView(APITestCase):
    file_name = 'features/tests/assets/test_file.csv'
    url = reverse('dataset-upload')
    zip_file_name = 'archive.zip'

    def test_upload_dataset(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        with zipfile.ZipFile(self.zip_file_name, 'w') as zip_file:
            zip_file.write(self.file_name)

        with patch('features.views.initialize_from_dataset.delay') as initialize_from_dataset_mock:
            with open(self.zip_file_name, 'rb') as file_data:
                response = self.client.put(self.url, {'file': file_data}, format='multipart')

            dataset = Dataset.objects.first()
            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.json(), DatasetSerializer(instance=dataset).data)
            self.assertEqual(dataset.name, self.file_name)
            self.assertEqual(dataset.uploaded_by, user)

            with open(self.file_name, 'rb') as file_data:
                self.assertEqual(dataset.content.read(), file_data.read())
            initialize_from_dataset_mock.assert_called_once_with(dataset_id=dataset.id)

    def test_upload_dataset_no_zip_file(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        with open(self.file_name) as file_data:
            response = self.client.put(self.url, {'file': file_data}, format='multipart')

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'detail': 'Uploaded file is not a zip file.'})

    def test_upload_dataset_no_csv_in_zip(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        empty_zip_data = b'PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
                         b'\x00\x00\x00\x00\x00\x00\x00'
        with open(self.zip_file_name, 'w+b') as zip_file:
            zip_file.write(empty_zip_data)

        with open(self.zip_file_name, 'rb') as zip_file:
            response = self.client.put(self.url, {'file': zip_file}, format='multipart')

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'detail': 'No CSV file found in ZIP archive.'})

    def test_upload_dataset_unauthenticated(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})

    def tearDown(self):
        # Remove that shitty file
        if os.path.isfile(self.zip_file_name):
            os.remove(self.zip_file_name)
            self.assertFalse(os.path.isfile(self.zip_file_name))


class TestFeatureListView(APITestCase):
    def test_retrieve_feature_list(self):
        user = UserFactory()
        self.client.force_authenticate(user)

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
        self.assertEqual(first_obj.pop('categories'), data['categories'])
        self.assertEqual(len(first_obj), 0)

    def test_retrieve_feature_list_dataset_not_found(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        url = reverse('dataset-features-list', args=['5781ca8a-3c7d-46b4-897e-90d80e938258'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_retrieve_feature_list_dataset_unauthenticated(self):
        url = reverse('dataset-features-list', args=['5781ca8a-3c7d-46b4-897e-90d80e938258'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestFeatureSamplesView(APITestCase):
    def test_retrieve_samples(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        sample = SampleFactory()

        url = reverse('feature-samples', args=[sample.feature.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        data = SampleSerializer(instance=sample).data
        json_data = response.json()
        self.assertEqual(len(json_data), 1)
        self.assertAlmostEqual(json_data.pop(0).pop('value'), data['value'])
        self.assertEqual(len(json_data), 0)

    def test_retrieve_samples_not_found(self):
        pass

    def test_retrieve_samples_not_authenticated(self):
        url = reverse('feature-samples', args=['9b1fe7e4-9bb7-4388-a1e4-40a35465d310'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestFeatureHistogramView(APITestCase):
    def test_retrieve_histogram(self):
        user = UserFactory()
        self.client.force_authenticate(user)

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
        user = UserFactory()
        self.client.force_authenticate(user)

        url = reverse('feature-histogram', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_retrieve_histogram_not_authenticated(self):
        url = reverse('feature-histogram', args=['9b1fe7e4-9bb7-4388-a1e4-40a35465d310'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestFeatureSlicesView(APITestCase):
    def test_retrieve_slices(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        test_data = {'key': 'dummy_data'}
        result_calculation_map = ResultCalculationMapFactory()
        features = [FeatureFactory(dataset=result_calculation_map.target.dataset), FeatureFactory(dataset=result_calculation_map.target.dataset)]
        fslice = SliceFactory(output_definition=test_data, features=features, result_calculation_map=result_calculation_map)
        request_data = {'features': [str(feature.id) for feature in features]}

        url = reverse('target-feature-slices',
                      args=[fslice.result_calculation_map.target.id])
        response = self.client.post(url, data=request_data, format='json')

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), test_data)

    def test_retrieve_slices_empty_body(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        
        target = FeatureFactory()
        features = [FeatureFactory(dataset=target.dataset), FeatureFactory(dataset=target.dataset)]
        request_data = {'features': [str(feature.id) for feature in features]}

        url = reverse('target-feature-slices',
                      args=[target.id])
        response = self.client.post(url, data=request_data, format='json')
        
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_retrieve_slices_feature_not_found(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        target = FeatureFactory()
        request_data = {'features': [str(uuid4())]}

        url = reverse('target-feature-slices', args=[target.id])
        response = self.client.post(url, data=request_data, format='json')

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_retrieve_slices_target_not_found(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        url = reverse('target-feature-slices', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_retrieve_slices_target_not_authenticated(self):
        url = reverse('target-feature-slices', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestFeatureRelevancyResultsView(APITestCase):
    def test_retrieve_relevancy_results(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        feature = FeatureFactory()
        relevancy = RelevancyFactory()
        relevancy.features.set([feature])

        url = reverse('target-feature-relevancy_results',
                      args=[relevancy.result_calculation_map.target.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        data = RelevancySerializer(instance=relevancy).data
        json_data = response.json()
        first_obj = json_data.pop(0)
        self.assertEqual(len(json_data), 0)
        self.assertEqual(first_obj.pop('id'), str(data['id']))
        self.assertEqual(str(first_obj.pop('features')), str([str(ft) for ft in data['features']]))
        self.assertAlmostEqual(first_obj.pop('relevancy'), data['relevancy'])
        self.assertAlmostEqual(first_obj.pop('iteration'), data['iteration'])
        self.assertEqual(len(first_obj), 0)

    def test_retrieve_relevancy_results_target_not_found(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        url = reverse('target-feature-relevancy_results',
                      args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_retrieve_relevancy_results_target_not_authenticated(self):
        url = reverse('target-feature-relevancy_results',
                      args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestFeatureRedundancyResults(APITestCase):
    def test_retrieve_redundancy_results(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        first_feature = FeatureFactory()
        result_calculation_map = ResultCalculationMapFactory(target=first_feature)
        second_feature = FeatureFactory(dataset=first_feature.dataset)
        redundancy = RedundancyFactory(first_feature=first_feature,
                                       second_feature=second_feature,
                                       result_calculation_map=result_calculation_map)
        serializer = RedundancySerializer(instance=redundancy)

        url = reverse('feature-redundancy_results',
                      args=[result_calculation_map.target.id])
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
        user = UserFactory()
        self.client.force_authenticate(user)

        url = reverse('feature-redundancy_results', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_retrieve_redundancy_results_dataset_not_authenticated(self):
        url = reverse('feature-redundancy_results', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestCondiditonalDistributionsView(APITestCase):
    def test_conditional_distributions_target_not_found(self):
        pass

    def test_conditional_distributions_feature_not_found(self):
        pass

    def test_conditional_distributions_missing_data(self):
        pass

    def test_conditional_distributions_not_authenticated(self):
        url = reverse('target-condidtional-distributions',
                      args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.post(url, data={}, format='json')

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})

    def test_conditional_distributions(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        target = FeatureFactory()
        feature = FeatureFactory(dataset=target.dataset)
        url = reverse('target-condidtional-distributions', args=[target.id])

        # Test for range
        data_range = [{
            'feature': feature.id,
            'range': {
                'from_value': -1,
                'to_value': 1
            }
        }]

        with patch('features.views.calculate_conditional_distributions.apply_async',) as task_mock:
            task_mock.get.return_value = []  # TODO: Proper data
            response = self.client.post(url, data=data_range, format='json')
            task_mock.assert_called_once_with(args=[target.id,data_range])
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [])

        # Test for categories
        data_categorical = [{
            'feature': feature.id,
            'categories': [1.0, 3.0]
        }]

        with patch('features.views.calculate_conditional_distributions.apply_async', ) as task_mock:
            task_mock.get.return_value = []  # TODO: Proper data
            response = self.client.post(url, data=data_categorical, format='json')
            task_mock.assert_called_once_with(args=[target.id, data_categorical])
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [])


class TestFeatureSpectrogramView(APITestCase):
    def test_retrieve_spectrogram(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        spectrogram = SpectrogramFactory()
        serializer = SpectrogramSerializer(instance=spectrogram)

        url = reverse('feature-spectrogram', args=[spectrogram.feature.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), serializer.data)

    def test_retrieve_spectrogram_not_found(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        url = reverse('feature-spectrogram', args=['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_retrieve_spectrogram_authenticated(self):
        url = reverse('feature-spectrogram', args=['9b1fe7e4-9bb7-4388-a1e4-40a35465d310'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class FixedFeatureSetHicsView(APITestCase):
    def test_fixed_feature_set_hics(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        target = FeatureFactory()
        feature1 = FeatureFactory(dataset=target.dataset)
        feature2 = FeatureFactory(dataset=target.dataset)
        result_calculation_map = ResultCalculationMapFactory(target=target)
        calculation = CalculationFactory(result_calculation_map=result_calculation_map)

        with patch('features.views.calculate_hics.apply_async') as task_mock, patch('features.views.Calculation.objects.create') as create_calculation:
            create_calculation.return_value = calculation

            url = reverse('fixed-feature-set-hics', args=[str(target.id)])
            response = self.client.post(url, data={'features': [feature1.id, feature2.id]}, format='json')

            task_mock.assert_called_once_with(kwargs={
                'calculation': calculation,
                'feature_ids': [feature1.id, feature2.id],
                'bivariate': False,
                'calculate_supersets': False,
                'calculate_redundancies': False})

            self.assertEqual(response.content, b'')
            self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

    def test_fixed_feature_set_hics_feature_not_found(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        target = FeatureFactory()
        result_calculation_map = ResultCalculationMapFactory(target=target)
        calculation = CalculationFactory(result_calculation_map=result_calculation_map)

        with patch('features.views.calculate_hics.apply_async') as task_mock, patch('features.views.Calculation.objects.create') as create_calculation:
            create_calculation.return_value = calculation
            url = reverse('fixed-feature-set-hics', args=[str(target.id)])
            response = self.client.post(url, data={'features': ['9b1fe7e4-9bb7-4388-a1e4-40a35465d310']}, format='json')

            task_mock.assert_not_called()

            self.assertEqual(response.json(), {'detail': 'Not found.'})
            self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_fixed_feature_set_hics_target_not_found(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        url = reverse('fixed-feature-set-hics', args=['9b1fe7e4-9bb7-4388-a1e4-40a35465d310'])
        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_fixed_feature_set_hics_not_authenticated(self):
        url = reverse('fixed-feature-set-hics', args=['9b1fe7e4-9bb7-4388-a1e4-40a35465d310'])
        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})