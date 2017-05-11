from channels.routing import route_class
from features.consumers import Demultiplexer


channel_routing = [
    route_class(Demultiplexer, path='^/bindings/?$'),
]
