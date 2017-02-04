from channels.generic.websockets import WebsocketDemultiplexer
from features.bindings import DatasetBinding, RedundancyResultBinding, RelevancyResultBinding


class Demultiplexer(WebsocketDemultiplexer):
    consumers = {
        'dataset': DatasetBinding.consumer,
        'relevancy_result': RelevancyResultBinding.consumer,
        'redundancy_result': RedundancyResultBinding.consumer
    }

    def connection_groups(self):
        return ['dataset-updates', 'relevancy-result-updates', 'redundancy-result-updates']
