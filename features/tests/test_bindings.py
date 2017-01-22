from channels.tests import ChannelTestCase, HttpClient
from channels.signals import consumer_finished
from features.tests.factories import RarResultFactory


class TestIntegerValueBinding(ChannelTestCase):
    def test_outbound_create(self):
        client = HttpClient()
        client.join_group('rarresult-updates')

        rar_result = RarResultFactory()

        consumer_finished.send(sender=None)
        received = client.receive()
        self.assertIsNotNone(received)

        self.assertTrue('payload' in received)
        self.assertTrue('action' in received['payload'])
        self.assertTrue('data' in received['payload'])
        self.assertTrue('relevancy' in received['payload']['data'])
        self.assertTrue('feature' in received['payload']['data'])
        self.assertTrue('rank' in received['payload']['data'])

        self.assertEqual(received['payload']['action'], 'update')
        self.assertEqual(received['payload']['model'], 'features.rarresult')
        self.assertEqual(received['payload']['pk'], str(rar_result.pk))

        self.assertEqual(received['payload']['data']['relevancy'], rar_result.relevancy)
        self.assertEqual(received['payload']['data']['rank'], rar_result.rank)
        self.assertEqual(received['payload']['data']['feature'], str(rar_result.feature.id))

        self.assertIsNone(client.receive())
