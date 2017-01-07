from channels.generic.websockets import JsonWebsocketConsumer

GROUP_NAME = 'features'


class EventConsumer(JsonWebsocketConsumer):
    strict_ordering = False
    slight_ordering = False

    def connection_groups(self, **kwargs):
        """
        Called to return the list of groups to automatically add/remove
        this connection to/from.
        """
        return [GROUP_NAME]
