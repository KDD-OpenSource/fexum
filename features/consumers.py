from channels.generic.websockets import WebsocketDemultiplexer
from features.bindings import DatasetBinding, CalculationBinding


class Demultiplexer(WebsocketDemultiplexer):
    http_user = True

    consumers = {
        'dataset': DatasetBinding.consumer,
        'calculation': CalculationBinding.consumer
    }

    def connection_groups(self, **kwargs):
        user = self.message.user

        if user.is_anonymous:
            return []

        user_groups = ['user-{0}-updates'.format(user.id)]

        return user_groups
