import time
import json
import os
from datetime import datetime
from functools import wraps

class ProductionMonitor:
    """Tracks performance and accuracy metrics in production."""
    def __init__(self, log_path: str = "nql/ml/data/telemetry_v3.jsonl"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_event(self, event_type: str, data: dict):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            **data
        }
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def track_performance(self):
        """Decorator to track function execution time."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = (time.time() - start) * 1000
                    self.log_event("performance", {
                        "function": func.__name__,
                        "duration_ms": round(duration, 2),
                        "status": "success"
                    })
                    return result
                except Exception as e:
                    duration = (time.time() - start) * 1000
                    self.log_event("performance", {
                        "function": func.__name__,
                        "duration_ms": round(duration, 2),
                        "status": "failure",
                        "error": str(e)
                    })
                    raise e
            return wrapper
        return decorator
