import asyncio
import importlib
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from bclib.utility import DictEx

if TYPE_CHECKING:  # pragma: no cover
    from .. import dispatcher as dispatcher_module


class CeleryManager:
    """Thin wrapper around celery.Celery that keeps the dependency optional."""

    def __init__(self, dispatcher: "dispatcher.IDispatcher", options: DictEx) -> None:
        self._dispatcher = dispatcher
        self._celery_options = options
        self._celery_app = self.__create_app(options)
        self._registered_tasks: dict[str, Any] = {}

    @property
    def app(self):
        return self._celery_app

    @property
    def tasks(self) -> dict[str, Any]:
        return self._registered_tasks

    @staticmethod
    def try_create(dispatcher: "dispatcher.IDispatcher", options: DictEx) -> Optional["CeleryManager"]:
        """Return a CeleryManager when celery is installed and configured."""
        celery_options = CeleryManager.__extract_options(options)
        if celery_options is None:
            return None
        try:
            importlib.import_module("celery")
        except ImportError:
            print(
                "Celery settings detected but 'celery' is not installed. "
                "Celery features are disabled. Install celery to enable them."
            )
            return None
        return CeleryManager(dispatcher, celery_options)

    @staticmethod
    def __extract_options(options: DictEx) -> Optional[DictEx]:
        """Extract celery block from options (router.celery or celery)."""
        if options.has("router") and isinstance(options.router, DictEx) and "celery" in options.router:
            return DictEx(options.router.celery)
        if "celery" in options:
            return DictEx(options.celery)
        return None

    def __create_app(self, celery_options: DictEx):
        from celery import Celery

        name = celery_options.name if celery_options.has("name") else "basisedge"
        broker = (
            celery_options.broker
            if celery_options.has("broker")
            else celery_options.broker_url if celery_options.has("broker_url") else None
        )
        backend = (
            celery_options.backend
            if celery_options.has("backend")
            else celery_options.result_backend if celery_options.has("result_backend") else None
        )
        include = celery_options.include if celery_options.has("include") else None

        app = Celery(name, broker=broker, backend=backend, include=include)

        # Merge additional celery configuration
        if celery_options.has("config") and isinstance(celery_options.config, dict):
            app.conf.update(**celery_options.config)
        if celery_options.has("task_routes"):
            app.conf.task_routes = celery_options.task_routes
        if celery_options.has("task_default_queue"):
            app.conf.task_default_queue = celery_options.task_default_queue
        if celery_options.has("task_queues") and isinstance(celery_options.task_queues, (list, tuple)):
            try:
                from kombu import Queue

                queues = []
                for q in celery_options.task_queues:
                    if isinstance(q, str):
                        queues.append(Queue(q))
                    elif isinstance(q, Dict):
                        queues.append(
                            Queue(
                                q.get("name"),
                                routing_key=q.get("routing_key"),
                                queue_arguments=q.get("arguments"),
                                exchange=q.get("exchange"),
                            )
                        )
                app.conf.task_queues = queues
            except Exception as ex:
                print(f"Could not configure Celery queues ({ex}); continuing without explicit queues.")
        return app

    def register_action(
        self,
        action_handler: Callable,
        *,
        task_name: Optional[str],
        queue: Optional[str],
        task_options: Optional[Dict[str, Any]] = None,
    ):
        """Register a handler function as a Celery task."""
        from bclib.context import CeleryContext

        if self._celery_app is None:
            return None

        options = dict(task_options or {})
        if queue:
            options.setdefault("queue", queue)
        name = task_name or action_handler.__name__

        @self._celery_app.task(name=name, bind=True, **options)
        def _task(task_self, *args, **kwargs):
            context = CeleryContext(
                task=task_self,
                dispatcher=self._dispatcher,
                args=list(args),
                kwargs=kwargs,
            )
            return self.__dispatch(context)

        self._registered_tasks[name] = _task
        return _task

    def __dispatch(self, context: "CeleryContext"):
        """Dispatch CeleryContext into dispatcher loop and return result."""
        loop = self._dispatcher.event_loop
        coroutine = self._dispatcher.dispatch_async(context)
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coroutine, loop)
            return future.result()
        return loop.run_until_complete(coroutine)
