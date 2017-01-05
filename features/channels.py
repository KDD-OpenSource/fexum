from channels.generic.websockets import JsonWebsocketConsumer


class EventConsumer(JsonWebsocketConsumer):
    strict_ordering = False
    slight_ordering = False
    GROUP_NAME = 'features'

    def connection_groups(self, **kwargs):
        """
        Called to return the list of groups to automatically add/remove
        this connection to/from.
        """
        return [self.GROUP_NAME]
