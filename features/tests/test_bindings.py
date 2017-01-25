from channels.tests import ChannelTestCase, HttpClient
from channels.signals import consumer_finished
from features.tests.factories import RelevancyResultFactory


class TestIntegerValueBinding(ChannelTestCase):
    def test_outbound_create(self):
        client = HttpClient()
        client.join_group('relevancy_result-updates')

        relevancy_result = RelevancyResultFactory()

        consumer_finished.send(sender=None)
        received = client.receive()
        self.assertIsNotNone(received)

        self.assertEqual(received['payload']['data'].pop('relevancy'), relevancy_result.relevancy)
        self.assertEqual(received['payload']['data'].pop('rank'), relevancy_result.rank)
        self.assertEqual(received['payload']['data'].pop('feature'), str(relevancy_result.feature.id))
        self.assertEqual(received['payload'].pop('data'), {})

        self.assertEqual(received['payload'].pop('action'), 'update')
        self.assertEqual(received['payload'].pop('model'), 'features.relevancyresult')
        self.assertEqual(received['payload'].pop('pk'), str(relevancy_result.pk))
        self.assertEqual(received.pop('payload'), {})

        self.assertEqual(received.pop('stream'), 'relevancy_result')

        self.assertEqual(received, {})
        self.assertIsNone(client.receive())
