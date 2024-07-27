import asyncio
import json
import random
from bclib import edge

main_service_options = {
    "server": "localhost:8080",
    "router": "web",
     "settings": {
        "connections.rest.service1": "http://localhost:8081",
        "connections.rest.service2": "http://localhost:8082",
        "connections.rest.service3": "http://localhost:8083",
        "connections.rest.service4": "http://localhost:8084",
        "connections.rest.service5": "http://localhost:8085",
        "connections.rest.service6": "http://localhost:8086"
    }
}
service1_options = {
    "server": "localhost:8081",
    "router": "restful"
}
service2_options = {
    "server": "localhost:8082",
    "router": "restful"
}
service3_options = {
    "server": "localhost:8083",
    "router": "restful"
}
service4_options = {
    "server": "localhost:8084",
    "router": "restful"
}
service5_options = {
    "server": "localhost:8085",
    "router": "restful"
}
service6_options = {
    "server": "localhost:8086",
    "router": "restful"
}

mani_app = edge.from_options(main_service_options)
service1_app = edge.from_options(service1_options,mani_app.event_loop)
service2_app = edge.from_options(service2_options,mani_app.event_loop)
service3_app = edge.from_options(service3_options,mani_app.event_loop)
service4_app = edge.from_options(service4_options,mani_app.event_loop)
service5_app = edge.from_options(service5_options,mani_app.event_loop)
service6_app = edge.from_options(service6_options,mani_app.event_loop)


@service1_app.restful_action(service1_app.url(":service_name"))
@service2_app.restful_action(service1_app.url(":service_name"))
@service3_app.restful_action(service1_app.url(":service_name"))
@service4_app.restful_action(service1_app.url(":service_name"))
@service5_app.restful_action(service1_app.url(":service_name"))
@service6_app.restful_action(service1_app.url(":service_name"))
async def process_web_action_async(context: edge.RequestContext):
    delay=random.randint(1,5)
    await asyncio.sleep(delay)
    return [{
        "id":random.randint(10,99),
        "message":f"Data 1 {context.url_segments.service_name} restful after {delay} sec..."
    },
    {
        "id":random.randint(10,99),
        "message":f"Data 2 {context.url_segments.service_name} restful after {delay} sec..."
    },
    {
        "id":random.randint(10,99),
        "message":f"Data 3 {context.url_segments.service_name} restful after {delay} sec..."
    },
    {
        "id":random.randint(10,99),
        "message":f"Data 4 {context.url_segments.service_name} restful after {delay} sec..."
    }]

@mani_app.web_action(mani_app.get("stream"))
async def process_web_action_async(context: edge.RESTfulContext):
    print("start")
    await context.start_stream_response_async(headers={'Content-Type': 'text/html; charset=utf-8'})
    await context.write_and_drain_async(b"start of data<br/>")
    count = 0
    while count<6:
        await context.write_and_drain_async("data is {0}...<br/>".format(count).encode())
        count+=1
        print(count)
        await asyncio.sleep(1)
    await context.write_and_drain_async(b"end of data")
    print("end")
    return True

@mani_app.web_action(mani_app.get("stream-2"))
async def process_web_action_async(context: edge.RESTfulContext):
    print("start")
    await context.start_stream_response_async( headers={'Content-Type': 'application/json; charset=utf-8'})
    await context.write_and_drain_async("[null,".encode())
    try:
        service_list =[
            ("service1",context.open_restful_connection("service1")),
            ("service2",context.open_restful_connection("service2")),
            ("service3",context.open_restful_connection("service3")),
            ("service4",context.open_restful_connection("service4")),
            ("service5",context.open_restful_connection("service5")),
            ("service6",context.open_restful_connection("service6")),
        ]   
        async def get_result_async(name:str, service:edge.RESTfulConnection):
            try:
                result = await service.get_async(f"/{name}")
            except Exception as ex:
                result = {"err" : str(ex)}
            data = {
                "sources": [
                {
                    "options": {
                    "tableName": "user.list",
                    "mergeType": 0 #MergeType append,
                    },
                    "data": result
                }],
            }
            await context.write_and_drain_async(json.dumps(data).encode())
            await context.write_and_drain_async(",".encode())
            
        tasks = [get_result_async(item[0],item[1]) for item in service_list]
        await asyncio.gather(*tasks)
        await context.write_and_drain_async("null]".encode())
        print("end")
        return True
    except asyncio.CancelledError as ex:
        return False
    except Exception as ex:
        print(ex)
        await context.write_and_drain_async(f"'{ex}',null]".encode())
        return False

@mani_app.web_action()
async def process_web_action_async(context: edge.WebContext):
    return "Hi from simple web server"

service1_app.listening(with_block=False)
service2_app.listening(with_block=False)
service3_app.listening(with_block=False)
service4_app.listening(with_block=False)
service5_app.listening(with_block=False)
service6_app.listening(with_block=False)
mani_app.listening()
