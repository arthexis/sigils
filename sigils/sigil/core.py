import re
import threading

from .render import RenderMixin
from .resolver import ResolverMixin


class Sigil(RenderMixin, ResolverMixin):
    """Parse and resolve lazy and eager sigil templates."""

    cache = threading.local()
    max_depth = 6
    debug = False

    def __init__(self, template, *, max_depth=None, debug=None):
        self._captured_secrets = {}
        self._captured_literals = {}
        self._template = str(template)
        self.max_depth = (
            max_depth if max_depth is not None else self.__class__.max_depth
        )
        self.debug = debug if debug is not None else self.__class__.debug
        self.pattern = re.compile(r"(?P<eager>%)?\[(?P<expression>.*?)\]")
        self._template = self._render_template(
            self._template,
            self._ambient_context(),
            eager_only=True,
        )


__all__ = ["Sigil"]
