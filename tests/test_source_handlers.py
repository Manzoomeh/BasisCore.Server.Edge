"""Source handler registration + dispatch."""
from bclib.context import (
    ClientSourceContext,
    ClientSourceMemberContext,
    ServerSourceContext,
    ServerSourceMemberContext,
)
from bclib.listener.http.http_message import HttpMessage

from helpers import cms_content, make_cms, run_dispatch

COMMAND = """
<basis core='dbsource' name='demo' source='basiscore'>
  <member name='list' type='list'></member>
</basis>
"""


def test_client_and_server_source_handlers(app):
    @app.client_source_handler()
    def client_src(context: ClientSourceContext):
        return [{"id": 1}]

    @app.client_source_member_handler()
    def client_member(context: ClientSourceMemberContext):
        return context.data

    @app.server_source_handler()
    def server_src(context: ServerSourceContext):
        return [{"id": 2}]

    @app.server_source_member_handler()
    def server_member(context: ServerSourceMemberContext):
        return context.data

    client_cms = make_cms(form={"command": COMMAND, "dmnid": "11"})
    server_cms = {"command": COMMAND, "dmnid": "22", "params": {}}

    client_result = run_dispatch(
        app, ClientSourceContext(client_cms, app, HttpMessage(client_cms))
    )
    server_result = run_dispatch(app, ServerSourceContext(server_cms, app))

    client_payload = cms_content(client_result)
    assert "sources" in client_payload
    assert client_payload["sources"][0]["data"] == [{"id": 1}]
    assert "sources" in server_result
    assert server_result["sources"][0]["data"] == [{"id": 2}]
