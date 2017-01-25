from channels.generic.websockets import WebsocketDemultiplexer
from features.bindings import RelevancyResultBinding, RedundancyResultBinding


class Demultiplexer(WebsocketDemultiplexer):
    consumers = {
        'relevancy_result': RelevancyResultBinding.consumer,
        'redundancy_result': RedundancyResultBinding.consumer
    }

    def connection_groups(self):
        return ['relevancy_result-updates', 'redundancy_result-updates']
