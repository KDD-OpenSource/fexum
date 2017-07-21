import os
import zipfile
from typing import Dict, Any, Callable
from unittest.mock import patch
from uuid import uuid4, UUID

from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT, \
    HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from rest_framework.test import APITestCase

from features.models import Experiment, Dataset, Calculation
from features.serializers import FeatureSerializer, BinSerializer, \
    DatasetSerializer, ExperimentSerializer, ExperimentTargetSerializer, \
    RelevancySerializer, RedundancySerializer, SpectrogramSerializer, CalculationSerializer
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, \
    DatasetFactory, ExperimentFactory, RelevancyFactory, RedundancyFactory, \
    ResultCalculationMapFactory, SpectrogramFactory, CalculationFactory, CurrentExperimentFactory
from users.tests.factories import UserFactory


class FexumAPITestCase(APITestCase):
    def _replace_uuids_by_strings(self, values_by_name: Dict) -> Dict:
        def _replace_uuid_by_string(value: Any) -> Any:
            if isinstance(value, UUID):
                return str(value)

            if isinstance(value, list):
                return [_replace_uuid_by_string(item) for item in value]

            return value

        return dict([(name, _replace_uuid_by_string(value=value)) for name, value in values_by_name.items()])

    def validate_error_on_unauthenticated(self, url_shortcut: str, request: Callable[[str], WSGIRequest],
                                          url_shortcut_args=[]):
        url = reverse(url_shortcut, args=url_shortcut_args)
        response = request(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestExperimentListView(FexumAPITestCase):
    def test_retrieve_experiment_list(self):
        experiment = ExperimentFactory()
        ExperimentFactory()  # Also just create create a second experiment with a different user

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

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(),
                         self._replace_uuids_by_strings(ExperimentSerializer(instance=experiment).data))

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
        self.validate_error_on_unauthenticated('experiment-list', lambda url: self.client.post(url, data={}))


class TestExperimentDetailView(FexumAPITestCase):
    def test_retrieve_experiment_detail(self):
        experiment = ExperimentFactory()
        self.client.force_authenticate(experiment.user)

        url = reverse('experiment-detail', args=[experiment.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(),
                         self._replace_uuids_by_strings(ExperimentSerializer(instance=experiment).data))

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
        self.validate_error_on_unauthenticated('experiment-detail', lambda url: self.client.get(url),
                                               ['079a60fc-c3b1-48ee-8bb6-ba19f061e9e0'])

    def test_patch_experiment_detail(self):
        experiment = ExperimentFactory()
        self.client.force_authenticate(experiment.user)

        visibility_text_filter = 'new_text'
        visibility_rank_filter = 11
        analysis_selection = [FeatureFactory(dataset=experiment.dataset)]
        visibility_blacklist = [FeatureFactory(dataset=experiment.dataset)]

        self.assertNotEqual(experiment.visibility_text_filter, visibility_text_filter)
        self.assertNotEqual(experiment.visibility_rank_filter, visibility_rank_filter)
        self.assertNotEqual(experiment.analysis_selection, analysis_selection)
        self.assertNotEqual(experiment.visibility_blacklist, visibility_blacklist)

        data = {
            'visibility_rank_filter': visibility_rank_filter,
            'visibility_text_filter': visibility_text_filter,
            'analysis_selection': [f.id for f in analysis_selection],
            'visibility_blacklist': [f.id for f in visibility_blacklist]
        }
        url = reverse('experiment-detail', args=[str(experiment.id)])

        response = self.client.patch(url, data)

        experiment = Experiment.objects.get(id=experiment.id)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(),
                         self._replace_uuids_by_strings(ExperimentSerializer(instance=experiment).data))
        self.assertEqual(experiment.visibility_text_filter, visibility_text_filter)
        self.assertEqual(experiment.visibility_rank_filter, visibility_rank_filter)
        self.assertEqual([experiment.analysis_selection.first()], analysis_selection)
        self.assertEqual([experiment.visibility_blacklist.first()], visibility_blacklist)

    def test_patch_experiment_invalid_data(self):
        experiment = ExperimentFactory()
        self.client.force_authenticate(experiment.user)

        data = {'visibility_blacklist': str(FeatureFactory().id)}

        url = reverse('experiment-detail', args=[str(experiment.id)])
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_patch_experiment_detail_not_found(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        experiment = ExperimentFactory()
        self.assertNotEqual(user, experiment.user)

        url = reverse('experiment-detail', args=[experiment.id])
        response = self.client.patch(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_patch_experiment_unauthenticated(self):
        self.validate_error_on_unauthenticated('experiment-detail', lambda url: self.client.patch(url),
                                               ['079a60fc-c3b1-48ee-8bb6-ba19f061e9e0'])


class TestTargetDetailView(FexumAPITestCase):
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
        self.validate_error_on_unauthenticated('experiment-targets-detail', lambda url: self.client.delete(url),
                                               ['1c6f46c4-e2d6-4378-8dc4-7417cca743da'])

    def test_select_target(self):
        experiment = ExperimentFactory(target=None)
        self.client.force_authenticate(experiment.user)

        target = FeatureFactory(dataset=experiment.dataset)
        result_calculation_map = ResultCalculationMapFactory(target=target)
        calculation = CalculationFactory(result_calculation_map=result_calculation_map)

        self.assertIsNone(experiment.target)
        self.assertEqual(experiment.dataset, target.dataset)

        url = reverse('experiment-targets-detail', args=[experiment.id])
        with patch('features.views.calculate_hics.subtask') as calculate_hics, patch(
                'features.views.Calculation.objects.create') as create_calculation:
            create_calculation.return_value = calculation

            response = self.client.put(url, data={'target': target.id}, format='json')

            self.assertEqual(response.status_code, HTTP_200_OK)

            experiment = Experiment.objects.get(id=experiment.id)
            data = ExperimentTargetSerializer(instance=experiment).data
            self.assertEqual(experiment.target, target)
            self.assertEqual(response.json(), {'target': str(data['target'])})
            calculate_hics.assert_called_once_with(immutable=True, kwargs={'calculation_id': str(calculation.id),
                                                                           'calculate_redundancies': True})
            # TODO: Test chain call

    def test_select_target_duplicated(self):
        experiment = ExperimentFactory(target=None)
        self.client.force_authenticate(experiment.user)

        target = FeatureFactory(dataset=experiment.dataset)
        result_calculation_map = ResultCalculationMapFactory(target=target)
        calculation = CalculationFactory(result_calculation_map=result_calculation_map,
                                         type=Calculation.DEFAULT_HICS)

        url = reverse('experiment-targets-detail', args=[experiment.id])
        with patch('features.views.calculate_hics.subtask') as calculate_hics:

            response = self.client.put(url, data={'target': target.id}, format='json')
            self.assertEqual(response.status_code, HTTP_200_OK)

            experiment = Experiment.objects.get(id=experiment.id)
            data = ExperimentTargetSerializer(instance=experiment).data
            calculation_count = Calculation.objects.filter(result_calculation_map=result_calculation_map,
                                                           type=Calculation.DEFAULT_HICS).count()

            self.assertEqual(calculation_count, 1)
            self.assertEqual(experiment.target, target)
            self.assertEqual(response.json(), {'target': str(data['target'])})
            self.assertFalse(calculate_hics.called)

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
        self.validate_error_on_unauthenticated('experiment-targets-detail', lambda url: self.client.put(url),
                                               ['1c6f46c4-e2d6-4378-8dc4-7417cca743da'])


class TestDatasetListView(FexumAPITestCase):
    def test_retrieve_all_datasets(self):
        user = UserFactory()

        dataset = DatasetFactory()

        url = reverse('dataset-list')
        self.client.force_authenticate(user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [DatasetSerializer(instance=dataset).data])

    def test_retrieve_all_datasets_unauthenticated(self):
        self.validate_error_on_unauthenticated('dataset-list', lambda url: self.client.get(url))


class TestDatasetUploadView(FexumAPITestCase):
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
        self.validate_error_on_unauthenticated('dataset-upload', lambda url: self.client.get(self.url))

    def tearDown(self):
        # Remove that shitty file
        if os.path.isfile(self.zip_file_name):
            os.remove(self.zip_file_name)
            self.assertFalse(os.path.isfile(self.zip_file_name))


class TestFeatureListView(FexumAPITestCase):
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
        self.assertAlmostEqual(first_obj.pop('max'), data['max'])
        self.assertAlmostEqual(first_obj.pop('variance'), data['variance'])
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
        self.validate_error_on_unauthenticated('dataset-features-list', lambda url: self.client.get(url),
                                               ['5781ca8a-3c7d-46b4-897e-90d80e938258'])


class TestFeatureSamplesView(FexumAPITestCase):
    def test_retrieve_samples(self):
        class get_mock():
            def get(self):
                return 'task_mock_return_value'

        user = UserFactory()
        self.client.force_authenticate(user)

        feature = FeatureFactory()
        max_samples = 1337

        with patch('features.views.get_samples.apply_async') as task_mock:
            task_mock.return_value = get_mock()

            url = reverse('feature-samples', args=[feature.id, max_samples])
            response = self.client.get(url)

            task_mock.assert_called_once_with(kwargs={
                'feature_id': str(feature.id),
                'max_samples': 1337
            })

            self.assertEqual(response.status_code, HTTP_200_OK)

            json_data = response.json()
            self.assertEqual(len(json_data), 22)
            self.assertEqual(json_data, 'task_mock_return_value')

    def test_retrieve_samples_not_found(self):
        pass

    def test_retrieve_samples_unauthenticated(self):
        self.validate_error_on_unauthenticated('feature-samples', lambda url: self.client.get(url), ['9b1fe7e4-9bb7-4388-a1e4-40a35465d310'])


class TestFeatureHistogramView(FexumAPITestCase):
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

    def test_retrieve_histogram_unauthenticated(self):
        self.validate_error_on_unauthenticated('feature-histogram', lambda url: self.client.get(url),
                                               ['9b1fe7e4-9bb7-4388-a1e4-40a35465d310'])


class TestFeatureSlicesView(FexumAPITestCase):
    def test_retrieve_slices(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        test_data = {'key': 'dummy_data'}
        result_calculation_map = ResultCalculationMapFactory()
        features = [FeatureFactory(dataset=result_calculation_map.target.dataset),
                    FeatureFactory(dataset=result_calculation_map.target.dataset)]
        fslice = SliceFactory(output_definition=test_data, features=features,
                              result_calculation_map=result_calculation_map)
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

    def test_retrieve_slices_target_unauthenticated(self):
        self.validate_error_on_unauthenticated('target-feature-slices', lambda url:  self.client.post(url), ['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])


class TestFeatureRelevancyResultsView(FexumAPITestCase):
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

    def test_retrieve_relevancy_results_target_unauthenticated(self):
        self.validate_error_on_unauthenticated('target-feature-relevancy_results', lambda url: self.client.get(url), ['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])


class TestFeatureRedundancyResults(FexumAPITestCase):
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

    def test_retrieve_redundancy_results_dataset_unauthenticated(self):
        self.validate_error_on_unauthenticated('feature-redundancy_results', lambda url: self.client.get(url), ['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])


class TestConditionalDistributionsView(FexumAPITestCase):
    def test_conditional_distributions_target_not_found(self):
        pass

    def test_conditional_distributions_feature_not_found(self):
        pass

    def test_conditional_distributions_missing_data(self):
        pass

    def test_conditional_distributions_unauthenticated(self):
        self.validate_error_on_unauthenticated('target-conditional-distributions', lambda url: self.client.post(url, data={}, format='json'), ['7a662af1-5cf2-4782-bcf2-02d601bcbb6e'])

    def test_conditional_distributions(self):
        class get_mock():
            def get(self):
                return {'task_mock_return_value': '1'}

        user = UserFactory()
        self.client.force_authenticate(user)

        target = FeatureFactory()
        feature = FeatureFactory(dataset=target.dataset)
        url = reverse('target-conditional-distributions', args=[target.id])

        data = [
            {
                'feature': feature.id,
                'range': {
                    'from_value': -1,
                    'to_value': 1
                },
            },
            {
                'feature': feature.id,
                'categories': [1.0, 3.0]
            }
        ]

        with patch('features.views.calculate_conditional_distributions.apply_async', ) as task_mock:
            task_mock.return_value = get_mock()
            response = self.client.post(url, data=data, format='json')
            task_mock.assert_called_once_with(args=[target.id, data, None])
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {'task_mock_return_value': '1'})

        # Test with max_samples
        max_samples = 2
        url = reverse('target-conditional-distributions', args=[target.id, max_samples])
        with patch('features.views.calculate_conditional_distributions.apply_async', ) as task_mock:
            task_mock.return_value = get_mock()
            response = self.client.post(url, data=data, format='json')
            task_mock.assert_called_once_with(args=[target.id, data, max_samples])
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {'task_mock_return_value': '1'})


class TestFeatureSpectrogramView(FexumAPITestCase):
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

    def test_retrieve_spectrogram_unauthenticated(self):
        self.validate_error_on_unauthenticated('feature-spectrogram', lambda url: self.client.get(url), ['9b1fe7e4-9bb7-at-a1e4-40a35465d310'])


class TestFixedFeatureSetHicsView(FexumAPITestCase):
    def test_fixed_feature_set_hics(self):
        user = UserFactory()
        self.client.force_authenticate(user)

        target = FeatureFactory()
        feature1 = FeatureFactory(dataset=target.dataset)
        feature2 = FeatureFactory(dataset=target.dataset)
        result_calculation_map = ResultCalculationMapFactory(target=target)
        calculation = CalculationFactory(result_calculation_map=result_calculation_map)

        with patch('features.views.calculate_hics.apply_async') as task_mock, patch(
                'features.views.Calculation.objects.create') as create_calculation:
            create_calculation.return_value = calculation

            url = reverse('fixed-feature-set-hics', args=[str(target.id)])
            response = self.client.post(url, data={'features': [feature1.id, feature2.id]}, format='json')

            task_mock.assert_called_once_with(kwargs={
                'calculation_id': str(calculation.id),
                'feature_ids': {str(feature1.id), str(feature2.id)},
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

        with patch('features.views.calculate_hics.apply_async') as task_mock, patch(
                'features.views.Calculation.objects.create') as create_calculation:
            create_calculation.return_value = calculation

            url = reverse('fixed-feature-set-hics', args=[str(target.id)])
            response = self.client.post(url, data={'features': ['9b1fe7e4-9bb7-4388-a1e4-40a35465d310']},
                                        format='json')

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

    def test_fixed_feature_set_hics_unauthenticated(self):
        self.validate_error_on_unauthenticated('fixed-feature-set-hics', lambda url: self.client.post(url), ['9b1fe7e4-9bb7-4388-a1e4-40a35465d310'])


class TestCalculationListView(FexumAPITestCase):
    def test_retrieve_calculations(self):
        user = UserFactory()

        calculation = CalculationFactory(max_iteration=2)

        url = reverse('calculation-list')
        self.client.force_authenticate(user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(),
                         [self._replace_uuids_by_strings(CalculationSerializer(instance=calculation).data)])

    def test_do_not_retrieve_done_calculations(self):
        user = UserFactory()

        CalculationFactory(max_iteration=5, current_iteration=5)

        url = reverse('calculation-list')
        self.client.force_authenticate(user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_retrieve_calculations_unauthenticated(self):
        self.validate_error_on_unauthenticated('calculation-list', lambda url: self.client.get(url))


class TestCurrentExperimentView(FexumAPITestCase):
    def test_retrieve_current_experiment_unauthenticated(self):
        self.validate_error_on_unauthenticated('current-experiment-detail', lambda url: self.client.get(url))

    def test_retrieve_current_experiment(self):
        user = UserFactory()
        current_experiment = CurrentExperimentFactory(user=user, experiment__user=user)

        url = reverse('current-experiment-detail')

        self.client.force_authenticate(user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(),
                         self._replace_uuids_by_strings(
                             ExperimentSerializer(instance=current_experiment.experiment).data))

    def test_retrieve_current_experiment_not_found(self):
        user = UserFactory()

        url = reverse('current-experiment-detail')

        self.client.force_authenticate(user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})


class TestSetCurrentExperimentView(FexumAPITestCase):
    def test_set_current_experiment_unauthenticated(self):
        self.validate_error_on_unauthenticated('set-current-experiment', lambda url: self.client.put(url), [
            '391ec5ac-f741-45c9-855a-7615c89ce128'])

    def test_set_current_experiment(self):
        user = UserFactory()
        experiment = ExperimentFactory(user=user)

        url = reverse('set-current-experiment', args=[str(experiment.id)])

        self.client.force_authenticate(user)
        response = self.client.put(url)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(),
                         self._replace_uuids_by_strings(ExperimentSerializer(instance=experiment).data))

    def test_set_current_experiment_not_found(self):
        user = UserFactory()
        # Belongs to someone else
        experiment = ExperimentFactory()

        url = reverse('set-current-experiment', args=[str(experiment.id)])

        self.client.force_authenticate(user)
        response = self.client.put(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})
