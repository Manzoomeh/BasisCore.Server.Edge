"""Thread-safe scheduling of background log coroutines."""
import asyncio
import concurrent.futures
from typing import Coroutine, Optional, Union

BackgroundLog = Union[asyncio.Task, concurrent.futures.Future]


def schedule_coroutine(coro: Coroutine, loop: Optional[asyncio.AbstractEventLoop] = None) -> BackgroundLog:
    """
    Schedule a coroutine on the application event loop from any thread.

    Sync handlers run in executor worker threads, where ``loop.create_task`` is not
    thread-safe and a loop obtained there is a new one that never runs. This helper:

    - returns ``loop.create_task(coro)`` when called on the loop's own thread;
    - uses ``asyncio.run_coroutine_threadsafe`` when called from another thread;
    - runs the coroutine to completion when no event loop is known at all, so the
      log is never silently dropped.

    Args:
        coro: Coroutine to run
        loop: Application event loop; defaults to the loop running in this thread

    Returns:
        asyncio.Task on the loop thread, otherwise a concurrent.futures.Future
    """
    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        running = None
    target = loop if loop is not None else running

    if target is None:
        # No application loop: send synchronously in this thread.
        done = concurrent.futures.Future()
        try:
            done.set_result(asyncio.run(coro))
        except BaseException as ex:
            done.set_exception(ex)
        return done

    if target is running:
        return target.create_task(coro)

    if target.is_closed():
        coro.close()
        done = concurrent.futures.Future()
        done.set_exception(RuntimeError("event loop is closed; background log dropped"))
        return done

    return asyncio.run_coroutine_threadsafe(coro, target)
