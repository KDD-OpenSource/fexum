from channels.tests import ChannelTestCase, HttpClient
from channels.signals import consumer_finished
from features.tests.factories import DatasetFactory, RarResultFactory


class TestDatasetBinding(ChannelTestCase):
    def test_outbound_create(self):
        client = HttpClient()
        client.join_group('dataset-updates')

        dataset = DatasetFactory()

        consumer_finished.send(sender=None)
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
        client = HttpClient()
        client.join_group('rar-result-updates')

        rar_result = RarResultFactory()

        consumer_finished.send(sender=None)
        received = client.receive()
        self.assertIsNotNone(received)

        self.assertEqual(received['payload']['data'].pop('id'), rar_result.id)
        self.assertEqual(received['payload'].pop('data'), {})

        self.assertEqual(received['payload'].pop('action'), 'update')
        self.assertEqual(received['payload'].pop('model'), 'features.rarresult')
        self.assertEqual(received['payload'].pop('pk'), str(rar_result.pk))
        self.assertEqual(received.pop('payload'), {})

        self.assertEqual(received.pop('stream'), 'rar_result')

        self.assertEqual(received, {})
        self.assertIsNone(client.receive())
