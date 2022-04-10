from bclib import edge
import business
import idb_manager


options = {
    "server": "localhost:8080",
    "router": "restful",
    "log_request": False,
    "settings": {
        "connections.sql.permissions": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.;DATABASE=MarketData;UID=sa;PWD=1234",
    }
}

app = edge.from_options(options)
db_manager = idb_manager.EdgeDbManager(app.db_manager)
manager = business.UserPermissionManager(db_manager)


@app.restful_action(
    app.url(":id"))
def process_user_permissions_request(context: edge.RESTfulContext):
    print("process_user_permissions_request")
    user_id = int(context.url_segments.id)
    request = business.UserPermissionRequest(user_id)
    return manager.get_user_permissions(request)


app.listening()
