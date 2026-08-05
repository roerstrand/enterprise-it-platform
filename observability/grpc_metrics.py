from functools import wraps
from prometheus_client import Histogram

GRPC_REQUEST_LATENCY = Histogram(
    "grpc_request_latency_seconds",
    "gRPC request latency in seconds",
    ["service", "method"],
)

def track_grpc_metrics(service_name):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, request, context):
            with GRPC_REQUEST_LATENCY.labels(service=service_name, method=func.__name__).time():
                return await func(self, request, context)
        return wrapper
    return decorator

