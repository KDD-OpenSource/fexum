from channels.routing import route_class, route
from features.consumers import Demultiplexer
from features.bindings import RelevancyBinding


channel_routing = [
    route_class(Demultiplexer, path='^/binding'),
    route('binding.relevancy', RelevancyBinding.consumer)
]
