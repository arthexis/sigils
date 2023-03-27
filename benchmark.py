import timeit

from sigils.parser import spool
from sigils.contexts import context


def time_spool_short():
    setup = """
from sigils.parser import spool
"""
    code = """
spool('[[USER]]')
"""
    result = timeit.timeit(code, number=1000000, setup=setup)
    print("spool (short):", result)


def time_spool_long():
    setup = """
from sigils.tools import spool
"""
    text = """
    Hello World, my name is [[PERSON.NAME]] and I'm [[PERSON.AGE]] years old.
    I live in [[PERSON.ADDRESS.CITY]], [[PERSON.ADDRESS.COUNTRY]].
    I'm a [[PERSON.JOB.TITLE]] at [[PERSON.JOB.COMPANY]].
    I'm married to [[PERSON.SPOUSE.NAME]] and we have [[PERSON.SPOUSE.CHILDREN]] children.
    """
    code = f"""
spool({text!r})
"""
    result = timeit.timeit(code, setup=setup, number=1000)
    print("spool (long):", result)


if __name__ == '__main__':
    time_spool_short()
    time_spool_long()

