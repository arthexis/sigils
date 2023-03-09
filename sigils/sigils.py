from .tools import splice, spool, vanish, unvanish
from .contexts import context


class Sigil(str):
    """Encapsulates a string or stream that may contain sigils.
    """

    def __init__(self, original: str, **context):
        self.original = original
        self.context = context

    def __str__(self):
        """Resolve the sigil with splice and return the resulting text."""
        return splice(self.original, **self.context)
    
    def __repr__(self):
        """Return a original representation of the text with sigils."""
        return self.original

    def __call__(self, *args, **kwargs):
        """Send all args and kwargs to context, then resolve."""
        with context(*args, **kwargs):
            return splice(self.original, **self.context)
        
    def __iter__(self):
        """Iterate over the sigils in the text."""
        return iter(spool(self.original))
    
    @property
    def sigils(self):
        """Return a list of sigils in the text."""
        return list(self)
    
    def clean(self, pattern: str):
        """Replace all sigils in the text with another pattern."""
        return vanish(self.original, pattern)
    
    def dirty(self, sigils: list, pattern: str):
        """De-replace all patterns in the text with sigils."""
        return unvanish(self.original, sigils, pattern)  # type: ignore



__all__ = ["Sigil"]
