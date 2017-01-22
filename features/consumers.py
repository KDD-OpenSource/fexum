from channels.generic.websockets import WebsocketDemultiplexer
from features.bindings import RarResultBinding


class Demultiplexer(WebsocketDemultiplexer):
    consumers = {
        'rar_result': RarResultBinding.consumer
    }

    def connection_groups(self):
        return ['rar_result-updates']
