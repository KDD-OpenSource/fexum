from channels import Group, route_class
from channels.tests import ChannelTestCase, Client, apply_routes
from features.channels import EventConsumer


class TestEventConsumer(ChannelTestCase):
    def test_send_relevancy_update(self):
        with apply_routes([route_class(EventConsumer, path='/socket')]):
            client = Client()
            client.consume('websocket.connect', {'path': '/socket'})
        
            Group("features").send({"text": 'a_text'})
        
            self.assertEqual(client.receive(), {'text': 'a_text'})
