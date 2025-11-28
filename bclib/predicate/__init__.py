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
    @app.action(route="/api/users/:id", method="GET")
    async def get_user(context):
        pass
    ```
"""

from bclib.predicate.all import All
from bclib.predicate.any import Any
from bclib.predicate.between import Between
from bclib.predicate.callback import Callback
from bclib.predicate.equal import Equal
from bclib.predicate.greater_than import GreaterThan
from bclib.predicate.greater_than_equal import GreaterThanEqual
from bclib.predicate.has_value import HasValue
from bclib.predicate.in_list import InList
from bclib.predicate.less_than import LessThan
from bclib.predicate.less_than_equal import LessThanEqual
from bclib.predicate.match import Match
from bclib.predicate.not_equal import NotEqual
from bclib.predicate.predicate import Predicate
from bclib.predicate.predicate_helper import PredicateHelper
from bclib.predicate.url import Url

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
