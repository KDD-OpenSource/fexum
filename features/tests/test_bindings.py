from channels.tests import ChannelTestCase, HttpClient
from channels.signals import consumer_finished
from features.tests.factories import RarResultFactory


class TestIntegerValueBinding(ChannelTestCase):
    def test_outbound_create(self):
        client = HttpClient()
        client.join_group('rar_result-updates')

        rar_result = RarResultFactory()

        consumer_finished.send(sender=None)
        received = client.receive()
        self.assertIsNotNone(received)

        self.assertEqual(received['payload']['data'].pop('relevancy'), rar_result.relevancy)
        self.assertEqual(received['payload']['data'].pop('redundancy'), rar_result.redundancy)
        self.assertEqual(received['payload']['data'].pop('rank'), rar_result.rank)
        self.assertEqual(received['payload']['data'].pop('feature'), str(rar_result.feature.id))
        self.assertEqual(received['payload'].pop('data'), {})

        self.assertEqual(received['payload'].pop('action'), 'update')
        self.assertEqual(received['payload'].pop('model'), 'features.rarresult')
        self.assertEqual(received['payload'].pop('pk'), str(rar_result.pk))
        self.assertEqual(received.pop('payload'), {})

        self.assertEqual(received.pop('stream'), 'rar_result')

        self.assertEqual(received, {})
        self.assertIsNone(client.receive())
