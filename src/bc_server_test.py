import asyncio
from socket_server import BasisCoreServer
from predicate import equal, in_list
from context import SourceContext, SourceMemberContext
from decorator import source_action, source_member_action


@source_action(
    equal("context.command.source", "basiscore"),
    in_list("context.command.mid", "10", "20"))
def process_demo_source(context: SourceContext):
    print("process1 ",  context)
    data = [
        {"id": 1, "name": "Data1"},
        {"id": 2, "name": "Data2"},
        {"id": 3, "name": "Data3"},
        {"id": 4, "name": "Data4"}
    ]
    context.data = data


@source_action(
    equal("context.command.source", "demo"),
    in_list("context.command.mid", "10", "20"))
def process_demo_source(context: SourceContext):
    print("process1 ",  context)
    data = [
        {"id": 44, "name": "Data 44", "age": 22},
        {"id": 66, "name": "Data 66", "age": 50},
        {"id": 76, "name": "Data 76", "age": 30},
        {"id": 89, "name": "Data 89", "age": 52},
        {"id": 70, "name": "Data 70", "age": 37},
        {"id": 40, "name": "Data 40", "age": 45}
    ]
    context.data = data


@source_member_action(
    equal("context.member.name", "list")
)
def process_list_member(context: SourceMemberContext):
    context.result = context.source_context.data
    print("process_list_member")


@source_member_action(
    equal("context.member.name", "paging")
)
def process_page_member(context: SourceMemberContext):
    data = {
        "total": len(context.source_context.data),
        "from": 0,
        "to": len(context.source_context.data)-1,
    }
    context.result = data
    print("process_page_member")


@source_member_action(
    equal("context.member.name", "count")
)
def process_count_member(context: SourceMemberContext):
    data = {
        "count": len(context.source_context.data)
    }
    context.result = data
    print("process_count_member")


@source_member_action()
def all_member_process(context: SourceMemberContext):
    context.result = None
    print("all_member_process", )


async def main():
    server = BasisCoreServer('127.0.0.1', 1025)
    await server.process_async()


asyncio.run(main())
