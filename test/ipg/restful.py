import random
from typing import Annotated

from bclib import edge
from bclib.edge import EdgeContainer
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from pasargad.pasargad_service import IPasargadService, PasargadService


options = {
    "server": "localhost:8080",
    "router": "restful",
    "log_request": False
}


@containers.copy(EdgeContainer)
class AppContainer(EdgeContainer):
    # app_resource1 = providers.Resource(manage_resource1)
    # app_resource2 = providers.Resource(manage_resource2_async)
    object_provider = providers.Callable(lambda: random.randint(100, 999))
    object_val = providers.Callable(lambda: random.randint(100, 999))
    object_val2 = providers.Callable(lambda: random.randint(1000, 9999))
    pasargad_service = providers.Singleton(
        PasargadService,
        config=EdgeContainer.app_config.ipg_providers.pasargad,
        dispatcher=EdgeContainer.dispatcher)


container = AppContainer()
container.app_config.from_dict({
    "server": "localhost:8080",
    "router": "restful",
    # "loop":asyncio.get_event_loop()
    "cache": {"1": 22},
    "ipg_providers": {
        "pasargad": {
            "terminalid": "70631433",
            "merchantid": "70604500",
            "username": "ERP7706718",
            "password": "w0#rDah?cy",
            "base_url": "https://pep.shaparak.ir/dorsa1"
        }
    }
})


app = edge.from_container(container)


@app.restful_action(app.get("get-token"))
@inject
async def process_default_web_action(context: edge.WebContext,  pasargad_Service: IPasargadService = Provide["pasargad_service"]):
    return await pasargad_Service.get_token_async()


@app.restful_action(app.get("get-purchase-url"))
@inject
async def get_token_async(context: edge.WebContext,  pasargad_Service: IPasargadService = Provide["pasargad_service"]):
    return await pasargad_Service.purchase_async("12", 1234, None)


@app.restful_action()
@inject
async def process_default_web_action(context: edge.WebContext):
    return "await process_default_web_action"


container.wire(modules=[__name__])
app.listening()
