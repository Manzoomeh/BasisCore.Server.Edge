"""
Example demonstrating RabbitConnection with exchange support

This example shows how to use RabbitConnection with both:
1. Direct queue publishing (original behavior)
2. Exchange with routing key (new feature)
"""

from bclib.db_manager.rabbit_connection import RabbitConnection
from bclib.utility import DictEx


def example_with_queue():
    """Example using direct queue (original behavior)"""
    print("Example 1: Publishing to Queue")
    print("-" * 50)

    # Configuration with queue
    config = DictEx({
        "host": "amqp://guest:guest@localhost:5672/",
        "queue": "my_queue",
        "durable": True
    })

    try:
        with RabbitConnection(config) as conn:
            # Publish message to queue
            message = {
                "type": "order",
                "data": {"order_id": "ORD-001", "amount": 100}
            }
            conn.publish(message)
            print(f"✓ Published to queue 'my_queue': {message}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()


def example_with_exchange():
    """Example using exchange with routing key (new feature)"""
    print("Example 2: Publishing to Exchange with Routing Key")
    print("-" * 50)

    # Configuration with exchange
    config = DictEx({
        "host": "amqp://guest:guest@localhost:5672/",
        "exchange": "orders_exchange",
        "durable": True
    })

    try:
        with RabbitConnection(config) as conn:
            # Publish message to exchange with routing key
            message = {
                "type": "order_created",
                "data": {"order_id": "ORD-002", "status": "pending"}
            }
            conn.publish(message, routing_key="orders.created")
            print(
                f"✓ Published to exchange 'orders_exchange' with routing key 'orders.created'")
            print(f"  Message: {message}")

            # Another message with different routing key
            message2 = {
                "type": "order_completed",
                "data": {"order_id": "ORD-003", "status": "completed"}
            }
            conn.publish(message2, routing_key="orders.completed")
            print(
                f"✓ Published to exchange 'orders_exchange' with routing key 'orders.completed'")
            print(f"  Message: {message2}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()


def example_invalid_config():
    """Example showing validation errors"""
    print("Example 3: Invalid Configurations")
    print("-" * 50)

    # Try to set both queue and exchange (should fail)
    try:
        config = DictEx({
            "host": "amqp://guest:guest@localhost:5672/",
            "queue": "my_queue",
            "exchange": "my_exchange"
        })
        conn = RabbitConnection(config)
        print("✗ Should have raised exception!")
    except Exception as e:
        print(f"✓ Correctly rejected: {e}")

    # Try to set neither queue nor exchange (should fail)
    try:
        config = DictEx({
            "host": "amqp://guest:guest@localhost:5672/"
        })
        conn = RabbitConnection(config)
        print("✗ Should have raised exception!")
    except Exception as e:
        print(f"✓ Correctly rejected: {e}")

    # Try to use routing_key with queue (should fail)
    try:
        config = DictEx({
            "host": "amqp://guest:guest@localhost:5672/",
            "queue": "my_queue"
        })
        with RabbitConnection(config) as conn:
            conn.publish({"data": "test"}, routing_key="test.key")
        print("✗ Should have raised exception!")
    except Exception as e:
        print(f"✓ Correctly rejected: {e}")

    print()


def show_configuration_guide():
    """Show configuration options"""
    print("Configuration Guide")
    print("=" * 70)
    print()

    print("Option 1: Direct Queue Publishing")
    print("-" * 70)
    print("""
config = DictEx({
    "host": "amqp://user:pass@host:5672/",
    "queue": "queue_name",           # Required (mutually exclusive with exchange)
    "passive": False,                # Optional
    "durable": True,                 # Optional
    "exclusive": False,              # Optional
    "auto_delete": False            # Optional
})

with RabbitConnection(config) as conn:
    conn.publish(message)            # No routing_key needed
""")

    print("Option 2: Exchange Publishing with Routing Key")
    print("-" * 70)
    print("""
config = DictEx({
    "host": "amqp://user:pass@host:5672/",
    "exchange": "exchange_name",     # Required (mutually exclusive with queue)
    "durable": True,                 # Optional
})

with RabbitConnection(config) as conn:
    conn.publish(message, routing_key="routing.key")  # routing_key required
""")

    print("Validation Rules")
    print("-" * 70)
    print("✓ Must specify either 'queue' OR 'exchange' (not both)")
    print("✓ Cannot use routing_key parameter when 'queue' is configured")
    print("✓ routing_key is optional when 'exchange' is configured")
    print("✓ Message encoding: UTF-8, ensure_ascii=False")
    print("✓ Content type: application/json")
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("RabbitConnection Exchange Support Examples")
    print("=" * 70)
    print()

    show_configuration_guide()

    print("\nNote: The following examples require a running RabbitMQ server")
    print("      Uncomment the function calls below to test with your RabbitMQ")
    print()

    # Uncomment these lines when you have RabbitMQ running:
    # example_with_queue()
    # example_with_exchange()
    example_invalid_config()

    print("=" * 70)
    print("Features Added:")
    print("  ✓ Exchange support (like RabbitSchemaBaseLogger)")
    print("  ✓ Routing key parameter in publish()")
    print("  ✓ Configuration validation")
    print("  ✓ UTF-8 encoding with ensure_ascii=False")
    print("  ✓ Proper message properties (content-type, encoding)")
    print("=" * 70)
