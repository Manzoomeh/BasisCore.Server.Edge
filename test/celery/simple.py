from datetime import timedelta
from bclib import edge

BROKER = "redis://127.0.0.1:6379/6"
RESULT_BACKEND = "redis://127.0.0.1:6379/7"
DEFAULT_QUEUE = "edge-default"
TASK_NAME = "edge_celery.run_demo"


options = {
    "server": "localhost:8080",
    "router": {
        "restful": ["*"],
        "celery": {
            "name": "edge_celery",
            "broker": BROKER,
            "backend": RESULT_BACKEND,
            "task_default_queue": DEFAULT_QUEUE,
            "task_routes": {
                TASK_NAME: {"queue": DEFAULT_QUEUE}
            },
            "task_queues": [DEFAULT_QUEUE],
            # برنامه زمان‌بندی‌شده برای celery beat: اجرای TASK_NAME هر 10 ثانیه
            "config": {
                "beat_schedule": {
                    "demo-every-10s": {
                        "task": TASK_NAME,
                        "schedule": timedelta(seconds=10),
                        "kwargs": {"scheduled": True}
                    }
                }
            }
        }
    }
}

app = edge.from_options(options)
# Expose for `celery -A test.celery.simple:celery_app worker`
celery_app = app.celery_app


@app.celery_action(task_name=TASK_NAME, queue=DEFAULT_QUEUE)
def process_celery_request(context: edge.CeleryContext):
    payload = context.kwargs or {}
    print('hi')
    return {
        "task": context.name,
        "task_id": context.task_id,
        "queue": context.queue,
        "payload": payload,
    }


@app.restful_action(app.post("api/celery/enqueue"))
def enqueue_via_rest(context: edge.RESTfulContext):
    if app.celery_app is None:
        return {"error": "celery is not configured or installed"}
    body = context.body if context.body else {}
    async_result = app.celery_app.send_task(TASK_NAME, kwargs=body)
    return {"task_id": async_result.id, "state": async_result.state}


if __name__ == "__main__":
    app.listening()
