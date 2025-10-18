import importlib

_registry: dict[str, type] = {}


class WorkerResolutionError(Exception):
    """Raised when a worker class cannot be resolved from a path string.

    This error occurs when the worker resolution process fails due to:

    - Invalid path format
    - Module not found or import errors
    - Class not found in the module
    - Resolved attribute is not a class
    """

    pass


def worker_name(cls: type) -> str:
    """Generate the fully qualified name for a worker class."""
    return f"{cls.__module__}.{cls.__qualname__}"


def register_worker(cls) -> None:
    """Register a worker class for usage later"""
    key = worker_name(cls)

    _registry[key] = cls


def resolve_worker(path: str) -> type:
    """Resolve a worker class by its path.

    Loads worker classes from the local registry, falling back to importing
    the module.

    Args:
        path: Fully qualified class path (e.g., "myapp.workers.EmailWorker")

    Returns:
        The resolved worker class

    Raises:
        WorkerResolutionError: If the worker cannot be resolved
    """
    if path in _registry:
        return _registry[path]

    parts = path.split(".")
    mod_name, cls_name = ".".join(parts[:-1]), parts[-1]

    try:
        mod = importlib.import_module(mod_name)
    except ModuleNotFoundError as error:
        raise WorkerResolutionError(
            f"Module '{mod_name}' not found for worker '{path}'"
        ) from error
    except ImportError as error:
        raise WorkerResolutionError(
            f"Failed to import module '{mod_name}' for worker '{path}'"
        ) from error

    try:
        cls = getattr(mod, cls_name)
    except AttributeError as error:
        raise WorkerResolutionError(
            f"Class '{cls_name}' not found in module '{mod_name}'"
        ) from error

    if not isinstance(cls, type):
        raise WorkerResolutionError(
            f"'{path}' resolved to {type(cls).__name__}, expected a class"
        )

    register_worker(cls)

    return cls
