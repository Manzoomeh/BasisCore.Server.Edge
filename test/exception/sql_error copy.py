from math import fabs

from bclib import edge

if "options" not in dir():
    options = {
        "server": "localhost:8080",
        "router": "web",
        "settings": {
            "connections.sql.sql_demo": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.;DATABASE=MarketData;UID=sa;PWD=1234",
            "connections.sqlite.sqlite_demo": "d:/sqlite.db",
            "connections.mongo.mongo_demo": "mongodb://localhost:27017/",
            "connections.rest.rest_demo": "http://127.0.0.1:5002/countries",
            "connections.rest.check_rkey": "https://trust-login.com/api2/checkrkey",
            "connections.rabbit.rabbit_test": {
                "host": "amqp://guest:guest@localhost:5672",
                "queue": "demo"
            }
        },
        "log_error": True,
        "log_request": False

    }


app = edge.from_options(options)


@app.web_handler()
def process_default_web_handler(context: edge.HttpContext):
    sql_connection = context.open_sql_connection("sql_demo")
    sqlite_connection = context.open_sqllite_connection("sqlite_demo")
    with sqlite_connection, sqlite_connection:
        with sql_connection.connection.cursor() as cursor:
            rows = cursor.execute("""
        SELECT TOP (10) [Id]
            ,[InsCode]
            ,[ISIN]
            ,[CISIN]
            ,[Name]
            ,[Symbol]
        FROM [MarketData].[dbo].[Shares]""").fetchall()
    print(rows)


app.listening()
