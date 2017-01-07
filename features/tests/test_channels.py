from channels import Group
from channels.tests import ChannelTestCase


class TestEventConsumer(ChannelTestCase):
    def test_send_relevancy_update(self):
        Group("test-group").add("test-channel")
        # Send to the group
        Group("test-group").send({"value": 42})
        # Verify the message got into the destination channel
        result = self.get_next_message("test-channel", require=True)
        self.assertEqual(result['value'], 42)
