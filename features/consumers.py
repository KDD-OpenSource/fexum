from channels.generic.websockets import WebsocketDemultiplexer
from features.bindings import RelevancyBinding

class Demultiplexer(WebsocketDemultiplexer):
    mapping = {
        'relevancy': RelevancyBinding.consumer
    }

    def connection_groups(self):
        return ['binding.values']
