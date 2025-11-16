from typing import Any, Dict, Optional, TYPE_CHECKING

from ..context.context import Context

if TYPE_CHECKING:
    from celery.app.task import Task
    from .. import dispatcher


class CeleryContext(Context):
    """Context passed to functions decorated by @app.celery_action."""

    def __init__(
        self,
        task: "Task",
        dispatcher: "dispatcher.IDispatcher",
        args: list[Any],
        kwargs: Dict[str, Any],
    ) -> None:
        super().__init__(dispatcher)
        self.task = task
        self.request = getattr(task, "request", None)
        self.args = args
        self.kwargs = kwargs
        self.is_adhoc = False
        self.url = getattr(self.request, "task", None)

    @property
    def task_id(self) -> Optional[str]:
        return getattr(self.request, "id", None) if self.request else None

    @property
    def name(self) -> Optional[str]:
        if self.request and hasattr(self.request, "task"):
            return self.request.task
        return getattr(self.task, "name", None)

    @property
    def queue(self) -> Optional[str]:
        if self.request and hasattr(self.request, "delivery_info"):
            return self.request.delivery_info.get("routing_key")
        return None

    @property
    def retries(self) -> Optional[int]:
        return getattr(self.request, "retries", None) if self.request else None

    @property
    def eta(self) -> Optional[str]:
        return getattr(self.request, "eta", None) if self.request else None

    @property
    def headers(self) -> Optional[Dict[str, Any]]:
        return getattr(self.request, "headers", None) if self.request else None

    def generate_response(self, result: Any) -> Any:
        """Celery tasks return raw result; no transformation required."""
        return result
