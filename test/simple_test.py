"""Simple test to debug handler registration"""
from bclib import edge
from bclib.context import RESTfulContext

options = {
    "server": "localhost:8098",
    "router": "restful",
    "log_error": True
}

app = edge.from_options(options)

print(f"App created: {app}")
print(f"App type: {type(app)}")


@app.restful_action(app.get("api/test"))
async def test_handler(context: RESTfulContext):
    return {"message": "Test handler works!"}

print("Handler registered")

# Check if handler is registered
lookup = app._Dispatcher__look_up
print(f"\nRegistered context types: {list(lookup.keys())}")
if RESTfulContext in lookup:
    handlers = lookup[RESTfulContext]
    print(f"RESTfulContext handlers count: {len(handlers)}")
else:
    print("❌ No handlers for RESTfulContext!")

if __name__ == "__main__":
    print("\nStarting server on http://localhost:8098")
    print("Test: curl http://localhost:8098/api/test")
    app.listening()
