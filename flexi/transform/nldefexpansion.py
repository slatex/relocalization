from __future__ import annotations

import itertools

from flexi.parsing.document import Definition, DocText
from flexi.parsing.mast import MAst, TermRef


class DefReading(list[MAst]):
    """ A reading of a definition (one MAst for each sentence) """

    @staticmethod
    def from_definition(definition: Definition) -> list[DefReading]:
        sentences = [
            sentence
            for doctext in definition.find_children(lambda x: isinstance(x, DocText))
            for sentence in doctext.sentences  # type: ignore
        ]

        return [
            DefReading(list(prod))
            for prod in itertools.product(*sentences)
        ]



def expand_nldef(mast: MAst, symbol_to_expand: str, definition: Definition) -> list[MAst]:
    """
    Expands all occurrences of the given symbol in the MAST according to the definition.
    Returns a list of possible results (depending on the reading of the definition).
    """


    # iterate: find first occurrence of the symbol, expand it, repeat

    todo_list: list[MAst] = [mast]
    results: list[MAst] = []

    while todo_list:
        current_mast = todo_list.pop(0)

        term_ref = current_mast.find_child(lambda x: isinstance(x, TermRef) and x.value == symbol_to_expand)
        if term_ref is None:
            if current_mast not in results:
                results.append(current_mast)   # nothing left to expand
            continue

    return results