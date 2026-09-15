import re
import threading

from .bindings import DirectionalBindingMixin
from .budgeting import ResolutionBudgetMixin
from .call_placement_syntax import ColonlessCallPlacementMixin
from .callable_state import CallableStateMixin
from .colon_data import ColonDataMixin
from .introspection import IntrospectionMixin
from .interpretations import BoundedInterpretationMixin
from .precedence import ResolutionPrecedenceMixin
from .render import RenderMixin
from .resolver import ResolverMixin
from .sequences import SequenceMixin


class Sigil(
    RenderMixin,
    IntrospectionMixin,
    ColonDataMixin,
    ColonlessCallPlacementMixin,
    DirectionalBindingMixin,
    SequenceMixin,
    ResolutionBudgetMixin,
    BoundedInterpretationMixin,
    CallableStateMixin,
    ResolutionPrecedenceMixin,
    ResolverMixin,
):
    """Parse, resolve, and explain lazy and eager sigil templates."""

    cache = threading.local()
    max_depth = 6
    debug = False

    def __init__(self, template, *, max_depth=None, debug=None):
        self._captured_secrets = {}
        self._captured_literals = {}
        self._resolution_local = threading.local()
        self._template = str(template)
        self.max_depth = (
            max_depth if max_depth is not None else self.__class__.max_depth
        )
        self.debug = debug if debug is not None else self.__class__.debug
        self.pattern = re.compile(
            r"(?P<eager>%)?\["
            r"(?P<expression>(?:[^\[\]]|\[[^\[\]]*\])*)"
            r"\]"
        )
        self._template = self._render_template(
            self._template,
            self._ambient_context(),
            eager_only=True,
        )

    @property
    def _resolution_session(self):
        """Return the semantic session scoped to the current thread."""
        return getattr(self._resolution_local, "session", None)

    @_resolution_session.setter
    def _resolution_session(self, session):
        """Store the semantic session only for the current thread."""
        self._resolution_local.session = session

    @_resolution_session.deleter
    def _resolution_session(self):
        """Clear only the current thread's semantic session."""
        try:
            del self._resolution_local.session
        except AttributeError:
            pass


__all__ = ["Sigil"]
