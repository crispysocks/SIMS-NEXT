import logging
import time
from functools import wraps
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TraceStep:
    def __init__(self, service: str, method: str, input_data: Any, output_data: Any = None, duration_ms: float = 0):
        self.service = service
        self.method = method
        self.input_data = input_data
        self.output_data = output_data
        self.duration_ms = duration_ms
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "service": self.service,
            "method": self.method,
            "input": self.input_data,
            "output": self.output_data,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp
        }


class TraceService:
    _instance: Optional['TraceService'] = None
    _steps: list[TraceStep] = []

    @classmethod
    def get_instance(cls) -> 'TraceService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_step(self, service: str, method: str, input_data: Any, output_data: Any = None, duration_ms: float = 0):
        step = TraceStep(service, method, input_data, output_data, duration_ms)
        self._steps.append(step)
        logger.info(f"[{service}] {method} - {duration_ms:.1f}ms")

    def get_steps(self) -> list[TraceStep]:
        return self._steps

    def clear(self):
        self._steps.clear()

    @staticmethod
    def traceable(service_name: str):
        """装饰器：为服务方法自动添加trace"""
        def decorator(method):
            @wraps(method)
            def wrapper(*args, **kwargs):
                trace = TraceService.get_instance()
                start = time.time()

                # 简化输入日志（避免大对象）
                input_repr = str(args[1:])[:200] if len(args) > 1 else str(kwargs)[:200]

                try:
                    result = method(*args, **kwargs)
                    duration_ms = (time.time() - start) * 1000

                    # 简化输出日志
                    output_repr = str(result)[:200] if result else None

                    trace.add_step(
                        service=service_name,
                        method=method.__name__,
                        input_data=input_repr,
                        output_data=output_repr,
                        duration_ms=duration_ms
                    )
                    return result
                except Exception as e:
                    duration_ms = (time.time() - start) * 1000
                    trace.add_step(
                        service=service_name,
                        method=method.__name__,
                        input_data=input_repr,
                        output_data=f"ERROR: {str(e)}",
                        duration_ms=duration_ms
                    )
                    raise

            return wrapper
        return decorator


# 导出为模块级函数，方便import
traceable = TraceService.traceable


def get_trace_service() -> TraceService:
    return TraceService.get_instance()