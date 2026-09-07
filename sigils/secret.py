class Secret:
    """Wrap a sensitive value while redacting incidental representations."""

    __slots__ = ("_value",)

    REDACTED = "[REDACTED]"

    def __init__(self, value):
        """Store *value* without exposing it through ``str`` or ``repr``."""
        self._value = value

    def reveal(self):
        """Return the wrapped value for an explicitly trusted caller."""
        return self._value

    def __str__(self):
        """Return the redacted display form."""
        return self.REDACTED

    def __repr__(self):
        """Return a representation that never includes the wrapped value."""
        return f"Secret({self.REDACTED!r})"


__all__ = ["Secret"]
