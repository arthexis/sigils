import threading

# TODO: We should be able to directly set the global context without using it as a manager


class Context:
    _context = threading.local()

    def __init__(self, context):
        self.local_context = context

    def __enter__(self):
        self.old_context = getattr(self._context, 'value', {})
        self._context.value = self.local_context
        return self._context.value

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context.value = self.old_context


# TODO: Add a "contextual" decorator that resolves default strings and string arguments 


__all__ = ["Context"]
