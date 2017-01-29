from channels.generic.websockets import WebsocketDemultiplexer
from features.bindings import DatasetBinding


class Demultiplexer(WebsocketDemultiplexer):
    consumers = {
        'dataset': DatasetBinding.consumer,
    }

    def connection_groups(self):
        return ['dataset-updates']
