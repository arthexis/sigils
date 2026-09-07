import threading

# TODO: We should be able to directly set the global context without using it as a manager


class Context:
    local = threading.local()

    def __init__(self, context):
        self.init_context = context

    def __enter__(self):
        self.old_context = getattr(self.local, "value", {})
        self.local.value = self.init_context
        return self.local.value

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.local.value = self.old_context

    def __getitem__(self, key):
        return self.local.value[key]


# TODO: Add a "contextual" decorator that resolves default strings and string arguments

__all__ = ["Context"]
