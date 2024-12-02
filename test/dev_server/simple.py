import asyncio
import random
from bclib import edge
from bclib.edge import EdgeContainer
from dependency_injector import containers, providers
from dependency_injector.wiring import  Provide, inject

def manage_resource1():
    print("init tasks 1")
    yield
    print("stop tasks 1")
async def manage_resource2_async():
    await asyncio.sleep(.5)
    print("init tasks 2")
    yield None
    await asyncio.sleep(.5)
    print("stop tasks 2")

@containers.copy(EdgeContainer)
class AppContainer(EdgeContainer):
    app_resource1 = providers.Resource(manage_resource1)
    app_resource2 = providers.Resource(manage_resource2_async)
    object_provider = providers.Callable(lambda: random.randint(100,999))
    object_val = providers.Callable(lambda: random.randint(100,999))
    object_val2 = providers.Callable(lambda: random.randint(1000,9999))

container=AppContainer()
container.app_config.from_dict({
        "server": "localhost:8080",
        "router": "web",
        #"loop":asyncio.get_event_loop()
        "cache":{"1":22}
        })


app = edge.create_server(container)

async def check_async(context: edge.RequestContext):
    return context.url.endswith("app")

@app.web_action(app.callback(check_async))
def process_web_action(context: edge.WebContext):
    return "result from process_web_action"

@app.web_action()
@inject
def process_default_web_action(context: edge.WebContext,val=Provide["object_provider"],container:AppContainer =Provide["edge_container"]):
    return "result from process_default_web_action " + str(val or "?") +" "+ str(context.dispatcher.container.object_val()) + " "+ str(container.object_val2())


container.wire(modules=[__name__])
app.listening()
