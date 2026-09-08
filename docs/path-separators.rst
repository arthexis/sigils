Path and call separators
========================

Sigil expressions support three separator behaviors:

``.``
    Always means path traversal. For example, ``[health.errors]`` traverses
    ``health`` and then ``errors``.

space
    Tries path traversal first. If traversal cannot continue and the previous
    value is callable, Sigils falls back to the historical callable form. Thus
    ``[health errors]`` is equivalent to ``[health.errors]`` when ``health``
    exposes ``errors``, while ``[greet name]`` still calls ``greet`` with the
    resolved ``name`` value when ``greet.name`` cannot be traversed.

``:``
    Explicitly requires the left side to resolve to a callable and invokes it.
    ``[greet:name]`` calls ``greet`` with the resolved ``name`` value even if
    the callable itself exposes a traversable ``name`` attribute. ``[now:]``
    forces a zero-argument call. If the left side is not callable, the Sigil
    remains unresolved.

This keeps dotted expressions unambiguous, preserves existing space-separated
function calls, and gives callers an explicit way to choose call semantics.
