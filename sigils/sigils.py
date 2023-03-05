from .transforms import splice
from .contexts import local_context


class Sigil(str):
    """Encapsulate a string that can contain sigils.
    When an instance of this class has its __str__ method called,
    the text gets passed through resolve automatically.
    """

    def __init__(self, original: str, **kwargs):
        self.original = original
        self.kwargs = kwargs

    def __str__(self):
        """Resolve the sigil."""
        return splice(self.original, **self.kwargs)
    
    def __repr__(self):
        """Return a representation of the sigil."""
        return self.original

    def __call__(self, *args, **kwargs):
        """Send all args and kwargs to context, then resolve."""
        with local_context(*args, **kwargs):
            return splice(self.original, **self.kwargs)


__all__ = ["Sigil"]
