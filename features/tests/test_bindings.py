from channels.tests import ChannelTestCase, HttpClient
from channels.signals import consumer_finished
from features.tests.factories import DatasetFactory, RedundancyResultFactory, RelevancyResultFactory


class TestDatasetBinding(ChannelTestCase):
    def test_outbound_create(self):
        client = HttpClient()
        client.join_group('dataset-updates')

        dataset = DatasetFactory()

        consumer_finished.send(sender=None)
        received = client.receive()
        self.assertIsNotNone(received)

        self.assertEqual(received['payload']['data'].pop('name'), dataset.relevancy)
        self.assertEqual(received['payload']['data'].pop('status'), dataset.rank)
        self.assertEqual(received['payload'].pop('data'), {})

        self.assertEqual(received['payload'].pop('action'), 'update')
        self.assertEqual(received['payload'].pop('model'), 'features.dataset')
        self.assertEqual(received['payload'].pop('pk'), str(dataset.pk))
        self.assertEqual(received.pop('payload'), {})

        self.assertEqual(received.pop('stream'), 'dataset')

        self.assertEqual(received, {})
        self.assertIsNone(client.receive())



class TestRelevancyResultBinding(ChannelTestCase):
    def test_outbound_create(self):
        client = HttpClient()
        client.join_group('relevancy-result-updates')

        relevancy_result = RelevancyResultFactory()

        consumer_finished.send(sender=None)
        received = client.receive()
        self.assertIsNotNone(received)

        self.assertEqual(received['payload']['data'].pop('id'), relevancy_result.id)
        self.assertEqual(received['payload'].pop('data'), {})

        self.assertEqual(received['payload'].pop('action'), 'update')
        self.assertEqual(received['payload'].pop('model'), 'features.relevancyresult')
        self.assertEqual(received['payload'].pop('pk'), str(relevancy_result.pk))
        self.assertEqual(received.pop('payload'), {})

        self.assertEqual(received.pop('stream'), 'relevancy_result')

        self.assertEqual(received, {})
        self.assertIsNone(client.receive())


class TestRedundancyResultBinding(ChannelTestCase):
    def test_outbound_create(self):
        client = HttpClient()
        client.join_group('redundancy-result-updates')

        redundancy_result = RedundancyResultFactory()

        consumer_finished.send(sender=None)
        received = client.receive()
        self.assertIsNotNone(received)

        self.assertEqual(received['payload']['data'].pop('id'), redundancy_result.id)
        self.assertEqual(received['payload'].pop('data'), {})

        self.assertEqual(received['payload'].pop('action'), 'update')
        self.assertEqual(received['payload'].pop('model'), 'features.redundancyresult')
        self.assertEqual(received['payload'].pop('pk'), str(redundancy_result.pk))
        self.assertEqual(received.pop('payload'), {})

        self.assertEqual(received.pop('stream'), 'redundancy_result')

        self.assertEqual(received, {})
        self.assertIsNone(client.receive())
