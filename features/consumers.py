from channels.generic.websockets import WebsocketDemultiplexer
from features.bindings import DatasetBinding, RarResultBinding


class Demultiplexer(WebsocketDemultiplexer):

    consumers = {
        'dataset': DatasetBinding.consumer,
        'rar_result': RarResultBinding.consumer
    }

    def connection_groups(self):
        return ['dataset-updates',
                'rar-result-updates']
