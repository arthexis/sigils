from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class PendingCall:
    """A resolved callable still waiting for leading positional inputs."""

    function: Callable[..., Any]
    trailing_args: tuple[Any, ...] = ()
    leading_args: tuple[Any, ...] = ()
    missing: int = 1
    protected: bool = False

    def consume(self, value: Any, *, protected: bool = False):
        """Fill one missing leading positional input and invoke when complete."""
        leading_args = (*self.leading_args, value)
        remaining = self.missing - 1
        protected_result = self.protected or protected
        if remaining > 0:
            return PendingCall(
                function=self.function,
                trailing_args=self.trailing_args,
                leading_args=leading_args,
                missing=remaining,
                protected=protected_result,
            )
        return self.function(*leading_args, *self.trailing_args), protected_result
