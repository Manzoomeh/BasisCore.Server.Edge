"""
Complete Example: Using RabbitMQ Connection in Handlers
========================================================

This example demonstrates how to use IRabbitConnection in different types of handlers:
1. RESTful API Handler
2. WebSocket Handler  
3. RabbitMQ Listener Handler

The example implements a simple e-commerce notification system.
"""

from datetime import datetime
from typing import Any, Dict

from bclib import edge
from bclib.connections.mongo import IMongoConnection
from bclib.connections.rabbit import IRabbitConnection

# ============================================================================
# Service Classes (Business Logic)
# ============================================================================


class OrderService:
    """
    Service for handling orders with MongoDB and RabbitMQ integration.

    Uses:
    - MongoDB for storing orders
    - RabbitMQ for publishing order events
    """

    def __init__(
        self,
        db: IMongoConnection['database.orders'],
        event_rabbit: IRabbitConnection['rabbitmq.events']
    ):
        self.orders = db.get_collection('orders')
        self.event_rabbit = event_rabbit

    async def create_order(self, order_data: Dict[str, Any]) -> str:
        """Create a new order and publish event."""
        # Add timestamp
        order_data['created_at'] = datetime.now()
        order_data['status'] = 'pending'

        # Save to MongoDB
        result = self.orders.insert_one(order_data)
        order_id = str(result.inserted_id)

        # Publish order.created event
        self.event_rabbit.publish_async({
            'event': 'order.created',
            'order_id': order_id,
            'user_id': order_data['user_id'],
            'total': order_data['total'],
            'timestamp': datetime.now().isoformat()
        }, routing_key='order.created')

        return order_id

    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status and publish event."""
        result = self.orders.update_one(
            {'_id': order_id},
            {'$set': {
                'status': status,
                'updated_at': datetime.now()
            }}
        )

        if result.modified_count > 0:
            # Publish status update event
            self.event_rabbit.publish_async({
                'event': 'order.status_changed',
                'order_id': order_id,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }, routing_key=f'order.{status}')

            return True
        return False


class NotificationService:
    """
    Service for sending notifications via different channels.

    Uses RabbitMQ queues for:
    - Email notifications
    - SMS notifications
    - Push notifications
    """

    def __init__(
        self,
        email_rabbit: IRabbitConnection['rabbitmq.email'],
        sms_rabbit: IRabbitConnection['rabbitmq.sms'],
        push_rabbit: IRabbitConnection['rabbitmq.push']
    ):
        self.email_rabbit = email_rabbit
        self.sms_rabbit = sms_rabbit
        self.push_rabbit = push_rabbit

    async def send_order_confirmation(self, order_id: str, user_email: str):
        """Send order confirmation via multiple channels."""
        # Email notification
        self.email_rabbit.publish_to_queue({
            'to': user_email,
            'subject': 'Order Confirmation',
            'template': 'order_confirmation',
            'data': {'order_id': order_id}
        })

        # SMS notification
        self.sms_rabbit.publish_to_queue({
            'phone': user_email,  # Should be phone number
            'message': f'Your order {order_id} has been confirmed!'
        })

        # Push notification
        self.push_rabbit.publish_to_queue({
            'user_id': user_email,
            'title': 'Order Confirmed',
            'body': f'Order #{order_id} confirmed',
            'data': {'order_id': order_id}
        })


class EventProcessor:
    """
    Service for processing events from RabbitMQ.

    This would typically run as a background worker consuming from RabbitListener.
    """

    def __init__(
        self,
        db: IMongoConnection['database.events'],
        notification_service: NotificationService
    ):
        self.events = db.get_collection('events')
        self.notification_service = notification_service

    async def process_order_event(self, event: Dict[str, Any]):
        """Process order-related events."""
        # Store event in MongoDB
        event['processed_at'] = datetime.now()
        self.events.insert_one(event)

        # Handle different event types
        if event['event'] == 'order.created':
            await self.notification_service.send_order_confirmation(
                event['order_id'],
                event.get('user_email', 'user@example.com')
            )
        elif event['event'] == 'order.status_changed':
            # Handle status change
            pass


# ============================================================================
# Handler Classes (API Endpoints)
# ============================================================================

class OrderRESTfulHandler:
    """
    RESTful API Handler for Order operations.

    Endpoints:
    - POST /api/orders - Create new order
    - PUT /api/orders/{order_id}/status - Update order status
    """

    def __init__(self, order_service: OrderService):
        self.order_service = order_service

    async def create_order(self, context: edge.RESTfulContext):
        """Handle POST /api/orders"""
        # Get request body
        order_data = context.get_request_body()

        # Validate
        if not order_data.get('user_id') or not order_data.get('items'):
            return {
                'success': False,
                'error': 'Missing required fields'
            }

        # Create order (will publish to RabbitMQ automatically)
        order_id = await self.order_service.create_order(order_data)

        return {
            'success': True,
            'order_id': order_id,
            'message': 'Order created and event published'
        }

    async def update_status(self, context: edge.RESTfulContext):
        """Handle PUT /api/orders/{order_id}/status"""
        order_id = context.get_parameter('order_id')
        status_data = context.get_request_body()

        success = await self.order_service.update_order_status(
            order_id,
            status_data['status']
        )

        return {
            'success': success,
            'message': 'Status updated' if success else 'Order not found'
        }


class OrderWebSocketHandler:
    """
    WebSocket Handler for real-time order updates.

    Allows clients to receive real-time notifications about their orders.
    """

    def __init__(
        self,
        order_service: OrderService,
        realtime_rabbit: IRabbitConnection['rabbitmq.realtime']
    ):
        self.order_service = order_service
        self.realtime_rabbit = realtime_rabbit

    async def handle_subscribe(self, context: edge.WebSocketContext):
        """Handle subscription to order updates."""
        message = context.get_request_body()
        order_id = message.get('order_id')

        # Publish subscription event
        self.realtime_rabbit.publish_async({
            'action': 'subscribe',
            'order_id': order_id,
            'connection_id': context.get_connection_id(),
            'timestamp': datetime.now().isoformat()
        }, routing_key=f'realtime.subscribe.{order_id}')

        return {
            'success': True,
            'message': f'Subscribed to order {order_id}'
        }


class EventRabbitHandler:
    """
    RabbitMQ Listener Handler for processing events.

    This handler receives events from RabbitListener and processes them.
    """

    def __init__(self, event_processor: EventProcessor):
        self.event_processor = event_processor

    async def handle_event(self, context: edge.RabbitContext):
        """Process incoming RabbitMQ messages."""
        # Get message from RabbitListener
        event = context.get_request_body()

        # Process the event
        await self.event_processor.process_order_event(event)

        return {
            'status': 'processed',
            'event': event.get('event'),
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# Application Setup
# ============================================================================

def setup_application():
    """
    Complete application setup example.
    """

    # Configuration
    options = {
        # MongoDB connections
        "database": {
            "orders": {
                "connection_string": "mongodb://localhost:27017",
                "database_name": "ecommerce_orders"
            },
            "events": {
                "connection_string": "mongodb://localhost:27017",
                "database_name": "ecommerce_events"
            }
        },

        # RabbitMQ connections
        "rabbitmq": {
            # Event exchange (pub/sub)
            "events": {
                "url": "amqp://guest:guest@localhost:5672/",
                "exchange": "order_events",
                "exchange_type": "topic",
                "routing_key": "order.*",
                "durable": True
            },

            # Notification queues
            "email": {
                "url": "amqp://guest:guest@localhost:5672/",
                "queue": "email_notifications",
                "durable": True
            },
            "sms": {
                "url": "amqp://guest:guest@localhost:5672/",
                "queue": "sms_notifications",
                "durable": True
            },
            "push": {
                "url": "amqp://guest:guest@localhost:5672/",
                "queue": "push_notifications",
                "durable": True
            },

            # Real-time updates
            "realtime": {
                "url": "amqp://guest:guest@localhost:5672/",
                "exchange": "realtime_updates",
                "exchange_type": "topic",
                "routing_key": "realtime.*",
                "durable": False
            }
        },

        # RabbitListener configuration (for consuming)
        "rabbit": [
            {
                "url": "amqp://guest:guest@localhost:5672/",
                "exchange": "order_events",
                "routing_key": "order.*",
                "exchange_type": "topic"
            }
        ],

        # HTTP server
        "http": "localhost:8080",
        "router": "restful"
    }

    # Create application
    app = edge.from_options(options)

    # Register RESTful handlers
    @app.restful_handler(app.url("api/orders"))
    async def handle_create_order(context: edge.RESTfulContext):
        handler = context.get_service(OrderRESTfulHandler)
        return await handler.create_order(context)

    @app.restful_handler(app.url("api/orders/{order_id}/status"))
    async def handle_update_status(context: edge.RESTfulContext):
        handler = context.get_service(OrderRESTfulHandler)
        return await handler.update_status(context)

    # Register WebSocket handler
    @app.websocket_handler(app.url("ws/orders"))
    async def handle_websocket(context: edge.WebSocketContext):
        handler = context.get_service(OrderWebSocketHandler)
        return await handler.handle_subscribe(context)

    # Register RabbitMQ handler
    @app.rabbit_handler()
    async def handle_rabbit_events(context: edge.RabbitContext):
        handler = context.get_service(EventRabbitHandler)
        return await handler.handle_event(context)

    # Start server
    app.listening()


if __name__ == "__main__":
    setup_application()


# ============================================================================
# Usage Examples
# ============================================================================

"""
1. Create Order (REST API):
   POST http://localhost:8080/api/orders
   Content-Type: application/json
   
   {
       "user_id": "user123",
       "items": [
           {"product_id": "prod1", "quantity": 2, "price": 29.99}
       ],
       "total": 59.98
   }
   
   Response:
   {
       "success": true,
       "order_id": "507f1f77bcf86cd799439011",
       "message": "Order created and event published"
   }

2. Update Order Status (REST API):
   PUT http://localhost:8080/api/orders/507f1f77bcf86cd799439011/status
   Content-Type: application/json
   
   {
       "status": "processing"
   }

3. Subscribe to Order Updates (WebSocket):
   ws://localhost:8080/ws/orders
   
   Send:
   {
       "order_id": "507f1f77bcf86cd799439011"
   }

4. RabbitMQ Flow:
   a) REST API creates order → publishes to "order_events" exchange
   b) RabbitListener receives event → calls EventRabbitHandler
   c) EventRabbitHandler processes → stores in MongoDB
   d) NotificationService sends notifications to email/sms/push queues
   e) Separate workers consume from notification queues
"""
