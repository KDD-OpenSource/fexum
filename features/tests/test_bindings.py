from channels.tests import ChannelTestCase, HttpClient

from features.models import Dataset, Calculation
from features.tests.factories import ExperimentFactory, CalculationFactory, DatasetFactory, FeatureFactory, \
    CurrentExperimentFactory, ResultCalculationMapFactory


class TestDatasetBinding(ChannelTestCase):
    def test_outbound_create(self):
        experiment = ExperimentFactory()
        CurrentExperimentFactory(experiment=experiment)

        client = HttpClient()
        client.force_login(experiment.user)
        client.join_group('user-{}-updates'.format(experiment.user_id))

        dataset = experiment.dataset
        dataset.status = Dataset.PROCESSING
        dataset.save()

        # It should not receive this one as it's not a current experiment
        ExperimentFactory(user=experiment.user)

        # It should not receive this one as it's on a different channel
        DatasetFactory()

        received = client.receive()
        self.assertIsNotNone(received)

        self.assertEqual(received['payload']['data'].pop('name'), dataset.name)
        self.assertEqual(received['payload']['data'].pop('status'), dataset.status)
        self.assertEqual(received['payload'].pop('data'), {})

        self.assertEqual(received['payload'].pop('action'), 'update')
        self.assertEqual(received['payload'].pop('model'), 'features.dataset')
        self.assertEqual(received['payload'].pop('pk'), str(dataset.pk))
        self.assertEqual(received.pop('payload'), {})

        self.assertEqual(received.pop('stream'), 'dataset')

        self.assertEqual(received, {})
        self.assertIsNone(client.receive())


class TestCalculationBinding(ChannelTestCase):
    def test_outbound_create(self):
        experiment = ExperimentFactory()
        CurrentExperimentFactory(experiment=experiment)

        client = HttpClient()
        client.force_login(experiment.user)
        client.join_group('user-{}-updates'.format(experiment.user_id))

        calculation = CalculationFactory(result_calculation_map__target=experiment.target,
                                         type=Calculation.RANDOM_FEATURE_SET_HICS)

        # It should not receive this one as it's not a current experiment
        ExperimentFactory(user=experiment.user)

        # It should not receive this one as it's on a different channel
        CalculationFactory()

        received = client.receive()
        self.assertIsNotNone(received)

        self.assertEqual(received['payload']['data'].pop('id'), str(calculation.id))
        self.assertEqual(received['payload']['data'].pop('current_iteration'), calculation.current_iteration)
        self.assertEqual(received['payload']['data'].pop('max_iteration'), calculation.max_iteration)
        self.assertEqual(received['payload']['data'].pop('type'), calculation.type)
        self.assertEqual(received['payload']['data'].pop('target'), str(calculation.result_calculation_map.target.id))
        self.assertEqual(received['payload']['data'].pop('features'), None)
        self.assertEqual(received['payload'].pop('data'), {})

        self.assertEqual(received['payload'].pop('action'), 'create')
        self.assertEqual(received['payload'].pop('model'), 'features.calculation')
        self.assertEqual(received['payload'].pop('pk'), str(calculation.pk))
        self.assertEqual(received.pop('payload'), {})

        self.assertEqual(received.pop('stream'), 'calculation')

        self.assertEqual(received, {})
        self.assertIsNone(client.receive())

    def test_outbound_create_fixed_feature_set(self):
        experiment = ExperimentFactory()
        CurrentExperimentFactory(experiment=experiment)

        client = HttpClient()
        client.force_login(experiment.user)
        client.join_group('user-{}-updates'.format(experiment.user_id))

        feature = FeatureFactory()
        result_calculation_map = ResultCalculationMapFactory(target=experiment.target)
        CalculationFactory(features=[feature],
                           result_calculation_map=result_calculation_map,
                           type=Calculation.FIXED_FEATURE_SET_HICS)

        # It should not receive this one as it's on a different channel
        CalculationFactory()

        received = client.receive()
        self.assertIsNotNone(received)

        self.assertEqual(received['payload']['data'].pop('features'), [str(feature.id)])

        self.assertIsNone(client.receive())
