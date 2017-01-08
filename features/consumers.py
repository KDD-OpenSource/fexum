from channels.generic.websockets import WebsocketDemultiplexer


class Demultiplexer(WebsocketDemultiplexer):
    mapping = {
        'relevancy': 'binding.relevancy'
    }

    def connection_groups(self):
        return ['binding.values']
