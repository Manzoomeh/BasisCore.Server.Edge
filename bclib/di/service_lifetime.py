"""
Service Lifetime - Service scope management

Defines how services are instantiated and their lifecycle:
- SINGLETON: One instance for entire application
- SCOPED: One instance per request/scope
- TRANSIENT: New instance every time
"""
from enum import Enum


class ServiceLifetime(Enum):
    """Service lifetime/scope management"""
    SINGLETON = "singleton"    # One instance for entire application
    SCOPED = "scoped"         # One instance per request/scope
    TRANSIENT = "transient"   # New instance every time
