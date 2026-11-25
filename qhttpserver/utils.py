from logging import Logger
from functools import wraps
from typing import Callable
from uuid import UUID
import re

MATCH = re.compile(r"<([a-zA-Z_]\w*)(?::([a-zA-Z]+))?>")
TYPES = {
    "int": (r"-?[0-9]+", int),
    "float": (r"-?[0-9]+(?:\.[0-9]+)?", float),
    "str": (r"[^/]+", str),
    "string": (r"[^/]+", str),
    "slug": (r"[A-Za-z0-9_-]+", str),
    "uuid": (r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}", UUID),
    "path": (r".+", str),
}


def check_regex(path: str) -> tuple[bool, str, dict]:
    path = path.rstrip("/")
    params: dict[str, Callable] = {}
    pattern, pos = "", 0

    for m in MATCH.finditer(path):
        name, group_type = m.groups()
        group_type = group_type or "str"
        if group_type not in TYPES:
            raise ValueError(f"Unknown path parameter type {group_type!r} in {path!r}")
        if name in params:
            raise ValueError(f"Duplicate path parameter {name!r} in {path!r}")

        regex, converter = TYPES[group_type]
        pattern += re.escape(path[pos : m.start()]) + f"(?P<{name}>{regex})"
        params[name] = converter
        pos = m.end()

    pattern += re.escape(path[pos:])
    return bool(params), rf"^{pattern}/?\Z", params


def pyqtSlot(logger: Logger | None = None):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                if logger is not None:
                    logger.exception(
                        f"An exception occured while running {func.__name__}",
                        exc_info=e,
                    )

        return wrapper

    return decorator
