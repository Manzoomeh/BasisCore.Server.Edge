"""
Predicate Package

Provides a comprehensive predicate system for request filtering and routing
in the BasisCore framework.

Features:
    - Comparison predicates (Equal, NotEqual, GreaterThan, LessThan, etc.)
    - Range checking (Between)
    - Pattern matching (Match, Url)
    - Logical combinators (All, Any)
    - Value validation (HasValue, InList)
    - Custom logic (Callback)
    - Factory methods (PredicateHelper)

Example:
    ```python
    from bclib.predicate import PredicateHelper, Equal, All
    
    # Using factory methods
    user_check = PredicateHelper.equal("context.query.user_id", "123")
    admin_check = PredicateHelper.in_list("context.query.role", "admin", "moderator")
    
    # Using classes directly
    status_check = Equal("context.query.status", "active")
    combined = All(status_check, admin_check)
    
    # Using in decorators
    @app.handler(route="/api/users/:id", method="GET")
    async def get_user(context):
        pass
    ```
"""

from .all import All
from .any import Any
from .between import Between
from .callback import Callback
from .equal import Equal
from .greater_than import GreaterThan
from .greater_than_equal import GreaterThanEqual
from .has_value import HasValue
from .in_list import InList
from .less_than import LessThan
from .less_than_equal import LessThanEqual
from .match import Match
from .not_equal import NotEqual
from .predicate import Predicate
from .predicate_helper import PredicateHelper
from .url import Url

__all__ = [
    # Base class
    'Predicate',

    # Comparison predicates
    'Equal',
    'NotEqual',
    'GreaterThan',
    'GreaterThanEqual',
    'LessThan',
    'LessThanEqual',
    'Between',

    # Pattern matching
    'Match',
    'Url',

    # Value validation
    'HasValue',
    'InList',

    # Logical combinators
    'All',
    'Any',

    # Custom logic
    'Callback',

    # Factory helper
    'PredicateHelper',
]
