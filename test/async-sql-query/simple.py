import asyncio
from bclib import edge



options = {
    "server": "localhost:8080",
    "router": "restful",
    "log_request": True,
    "settings": {
        "connections.sql.simple": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.;DATABASE=rond;UID=sa;PWD=1234",
    }
}

app = edge.from_options(options)




@app.restful_action(app.url("sample1"))
def process_user_permissions_request(context: edge.RESTfulContext):
    print("process_user_permissions_request")
    db = context.open_sql_connection('simple')
    with db:
        with db.connection.cursor() as cursor:
            rows = cursor.execute("SELECT rand() AS age;").fetchall()
            return [row.age for row in rows]


@app.restful_action()
async def process_user_permissions_request_async(context: edge.RESTfulContext):
    print("process_user_permissions_request")
    tasks= [get_data_async() for _ in range(10)]
    return await asyncio.gather(*tasks)

def get_data_async():
    def temp():
        db = app.db_manager.open_sql_connection('simple')
        with db:
            with db.connection.cursor() as cursor:
                rows = cursor.execute("SELECT rand() AS age;").fetchall()
                return [row.age for row in rows]
    return app.event_loop.run_in_executor(None,temp)

app.listening()
