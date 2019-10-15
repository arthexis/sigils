from lark import Lark

__all__ = ["parser"]

sigil_grammar = r"""
    start    : sigil
    sigil    : "[" node ("." node)* "]"
    node     : CNAME ["=" arg]
    arg      : sigil
             | "'" CNAME "'"
             | NUMBER

    %import common.CNAME
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

parser = Lark(sigil_grammar)
