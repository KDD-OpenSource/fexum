from channels.tests import ChannelTestCase, HttpClient
from features.tests.factories import ExperimentFactory, RarResultFactory, DatasetFactory
from features.models import Dataset


class TestDatasetBinding(ChannelTestCase):
    def test_outbound_create(self):
        experiment = ExperimentFactory()

        client = HttpClient()
        client.force_login(experiment.user)
        client.join_group('user-{}-updates'.format(experiment.user_id))

        dataset = experiment.dataset
        dataset.status = Dataset.PROCESSING
        dataset.save()

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


class TestRarResultBinding(ChannelTestCase):
    def test_outbound_create(self):
        experiment = ExperimentFactory()

        client = HttpClient()
        client.force_login(experiment.user)
        client.join_group('user-{}-updates'.format(experiment.user_id))

        rar_result = RarResultFactory(target=experiment.target)

        # It should not receive this one as it's on a different channel
        RarResultFactory()

        received = client.receive()
        self.assertIsNotNone(received)

        self.assertEqual(received['payload']['data'].pop('status'), rar_result.status)
        self.assertEqual(received['payload'].pop('data'), {})

        self.assertEqual(received['payload'].pop('action'), 'update')
        self.assertEqual(received['payload'].pop('model'), 'features.rarresult')
        self.assertEqual(received['payload'].pop('pk'), str(rar_result.pk))
        self.assertEqual(received.pop('payload'), {})

        self.assertEqual(received.pop('stream'), 'rar_result')

        self.assertEqual(received, {})
        self.assertIsNone(client.receive())
