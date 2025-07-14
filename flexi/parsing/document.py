from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Iterable, Callable

from lxml import etree

from flexi.parsing.magma import Sentence, MagmaGrammar


class DocNode:
    """ base class for all document nodes (should not be used directly) """

    def __init__(self, children: list[DocNode] = None):
        self.children = children if children is not None else []

    def find_children(
            self,
            filter: Callable[[DocNode], bool],
            recurse_on_match: bool = True,
    ) -> Iterable[DocNode]:
        if filter(self):
            yield self
            if not recurse_on_match:
                return
        for child in self.children:
            yield from child.find_children(filter, recurse_on_match)


class DocText(DocNode):
    def __init__(self, sentences: list[Sentence]):
        super().__init__()
        self.sentences = sentences


class Definition(DocNode):
    pass


class DocGroup(DocNode):
    pass


def ftml_to_doc(ftml: etree._Element | Path, grammar: MagmaGrammar) -> DocNode:
    if isinstance(ftml, Path):
        ftml = etree.parse(str(ftml)).getroot()

    result = ftml_to_doc_actual(deepcopy(ftml), grammar)
    # Still should simplify the result

    def _simplify(node: DocNode):
        new_children: list[DocNode] = []
        for child in node.children:
            new_child = _simplify(child)
            if isinstance(new_child, DocGroup):
                if not new_child.children:
                    continue
                if len(new_child.children) == 1 and isinstance(new_child.children[0], DocGroup):
                    new_child = new_child.children[0]
            if isinstance(new_child, DocText) and not new_child.sentences:
                continue
            new_children.append(new_child)
        node.children = new_children

    result = DocGroup([result])
    _simplify(result)
    return result.children[0]



def ftml_to_doc_actual(
        ftml: etree._Element,
        grammar: MagmaGrammar,
        run_sentence_extraction: bool = True,
) -> DocNode:
    """ breaks the DOM in the process -> pass clone """
    def _remove(element: etree._Element):
        """ remove element from its parent """
        new_node = etree.Element('span')
        new_node.tail = element.tail
        if element.getparent() is not None:
            element.getparent().replace(element, new_node)

    if 'data-ftml-definition' in ftml.attrib:
        ftml.attrib.clear()
        definition = Definition([ftml_to_doc_actual(ftml, grammar)])
        _remove(ftml)
        return definition

    children: list[DocNode] = []
    for child in ftml:
        children.append(ftml_to_doc_actual(child, grammar, run_sentence_extraction=False))

    if run_sentence_extraction:
        sentences = grammar.parse_ftml_to_sentences(ftml)
        if sentences:
            children.append(DocText(sentences))   # TODO: we lose the order here...

    return DocGroup(children)
