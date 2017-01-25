from channels.generic.websockets import WebsocketDemultiplexer
from features.bindings import RelevancyResultBinding


class Demultiplexer(WebsocketDemultiplexer):
    consumers = {
        'relevancy_result': RelevancyResultBinding.consumer
    }

    def connection_groups(self):
        return ['relevancy_result-updates']
