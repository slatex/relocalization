from __future__ import annotations

import re
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Optional

from flexi.gf.gfxml import GfXmlNode, GfNode, XmlNode, XmlText


class GfSymb(str):
    def __eq__(self, other) -> bool:
        if not isinstance(other, str):
            return False
        return str.__eq__(self, other) or \
            (other.startswith('regex:') and re.fullmatch(self, other[len('regex:'):]) is not None)


class MAst:
    """ A MAGMA AST node. (should never be instantiated directly) """
    __match_args__ = ('value', 'children')
    value: Any
    children: list[MAst]
    parent: Optional[MAst] = None
    parent_pos: Optional[int] = None   # position of this node in the parent's children list

    def __init__(self, value: Any, children: Optional[list[MAst]] = None):
        if self.__class__ == MAst:
            raise TypeError("MAst is an abstract class and cannot be instantiated directly")
        self.value = value
        self.children = children if children is not None else []
        for i, child in enumerate(self.children):
            if child.parent:
                raise ValueError("Child already has a parent")
            child.parent = self
            child.parent_pos = i

    def clone(self) -> MAst:
        """ Create a clone of this node. """
        clone = deepcopy(self)
        clone.parent = None
        clone.parent_pos = None
        return clone


class G(MAst):
    """ A GF AST node. """
    value: GfSymb

    def __init__(self, value: str, children: Optional[list[MAst]] = None):
        if isinstance(value, str):
            value = GfSymb(value)
        super().__init__(value, children)



class S(MAst, ABC):
    """ A semantic annotation node.

    We have various subclasses for different types of semantic annotations.
    """
    wrapfun: str    # needed for XML extension of Magma

    def __init__(self, value: str, children: Optional[list[MAst]] = None, wrapfun: Optional[str] = None):
        super().__init__(value, children)
        if not wrapfun:
            raise ValueError("wrapfun must be provided for semantic annotations")
        self.wrapfun = wrapfun

    @staticmethod
    @abstractmethod
    def try_from_gfxml(node: XmlNode) -> Optional[MAst]:
        pass

    @abstractmethod
    def to_gfxml(self) -> XmlNode:
        pass



class X(MAst):
    """ A decorative XML tag, i.e. a tag that does not carry semantic information we support """
    tag: str
    attrs: dict[str, str]
    wrapfun: str

    def __init__(self, tag: str, children: Optional[list[MAst]] = None, attrs: Optional[dict[str, str]] = None,
                 wrapfun: Optional[str] = None):
        super().__init__(tag, children)
        self.tag = tag
        self.attrs = attrs if attrs is not None else {}
        self.wrapfun = wrapfun if wrapfun is not None else ''


class M(MAst):
    """ A semantic math node.

    Example:
        The formula
            <mrow data-ftml-term="OMA" data-ftml-head="foo">
                <mi>bar</mi>
                <msqrt>
                    <mrow data-ftml-arg="1"><mi>baz</mi></mrow>
                </msqrt>
            </mrow>
        will result  in
            children = [MI('mi', [MT('baz')])]
            notation_pattern = [
                MI('mi', [MT('bar')]),
                MI('msqrt', [MathArg('1')])
            ]
    """
    value: str

    notation_pattern: list[MAst]

    def __init__(self, value: str, children: list[MAst], notation_pattern: list[MAst]):
        super().__init__(value, children)
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        self.notation_pattern = notation_pattern


class Formula(MAst):
    """ A formula node (i.e. <math> node) """
    __match_args__ = ('children',)
    value: None
    wrapfun: str

    def __init__(self, children: list[MAst], wrapfun: str):
        super().__init__(None, children)
        self.wrapfun = wrapfun


class MSeq(MAst):
    """ A sequence (as argument for a flexary operator) """
    __match_args__ = ('children',)
    value: None


class MathArg(MAst):
    """ Argument placeholder (only for notation patterns) """
    value: str


class MathSeqArg(MAst):
    """ Argument placeholder for a sequence (only for notation patterns) """
    value: str
    separator: Optional[MI] = None

    def add_arg(self, arg: MAst):
        arg = deepcopy(arg)
        arg.parent = self
        arg.parent_pos = len(self.children)
        self.children.append(arg)


class MI(MAst):
    """ A math node that is informal """
    value: str
    attrs: dict[str, str]

    def __init__(self, value: str, children: Optional[list[MAst]] = None, attrs: Optional[dict[str, str]] = None):
        super().__init__(value, children)
        self.attrs = attrs if attrs is not None else {}
        if not isinstance(value, str):
            raise TypeError("value must be a string")


class MT(MAst):
    """ MathML text content """
    __match_args__ = ('value',)
    value: str



# -----------------------------------
# classes for semantic annotations
# -----------------------------------


class TermRef(S):
    @staticmethod
    def try_from_gfxml(node: XmlNode) -> Optional[MAst]:
        if 'data-ftml-term' not in node.attrs:
            return None

        child = node.children[0]
        if isinstance(child, XmlNode) and 'data-ftml-comp' in child.attrs:
            node = child

        return TermRef(
            node.attrs['data-ftml-head'],
            [gf_xml_to_mast(child) for child in node.children],
            wrapfun=node.wrapfun
        )

    def to_gfxml(self) -> XmlNode:
        attrs = {'data-ftml-head': self.value, 'data-ftml-term': 'OMID'}
        return XmlNode(
            'span',
            [XmlNode(
                'span',
                [mast_to_gfxml(child) for child in self.children],
                attrs={'data-ftml-comp': '', 'class': 'ftml-comp'},
                wrapfun=self.wrapfun
            )],
            attrs,
            wrapfun=self.wrapfun
        )

class TermDef(S):
    """ definiendum """
    @staticmethod
    def try_from_gfxml(node: XmlNode) -> Optional[MAst]:
        if 'data-ftml-definiendum' not in node.attrs:
            return None

        return TermDef(
            node.attrs['data-ftml-definiendum'],
            [gf_xml_to_mast(child) for child in node.children],
            wrapfun=node.wrapfun
        )

    def to_gfxml(self) -> XmlNode:
        return XmlNode(
            'span',
            [mast_to_gfxml(child) for child in self.children],
            {'data-ftml-definiendum': self.value},
            wrapfun=self.wrapfun
        )


_ANNOS : list[type[S]] = [
    TermRef,
    TermDef,
]




def process_math_sem_node(nodes: list[GfXmlNode]) -> tuple[list[MAst], list[tuple[str, MAst]]]:
    """ returns (notation, argument values).
    argument values are tuples of (arg_num, arg_value).
    They should be sorted and grouped afterwards (syntactic order may differ from semantic order).
    TODO: this is somewhat ad-hoc... Not very robust and probably does not cover all cases.
    """

    notations: list[MAst] = []
    args: list[tuple[str, MAst]] = []

    for node in nodes:
        match node:
            case XmlNode(tag, children) if 'data-ftml-arg' in node.attrs:
                assert tag == 'mrow', f"Expected 'mrow' tag for math arg node, got {tag}"
                argno = node.attrs['data-ftml-arg']
                notations.append(MathArg(argno))
                assert len(children) == 1, f"Expected exactly one child for math arg node, got {len(children)}"
                args.append((argno, gf_xml_math_to_mast(children[0])))
            case XmlNode(tag, children) as x:
                # part of the notation
                _children2, _args2 = process_math_sem_node(children)
                args.extend(_args2)
                notations.append(MI(tag, _children2, x.attrs))
            case XmlText(text):
                notations.append(MT(text))
            case _:
                raise ValueError(f"Unexpected math node: {node}")

    # post-process: check if we actually had a sequence argument
    if any(isinstance(n, MathArg) and len(n.value) > 1 for n in notations):
        # it should be a sequence argument
        argmarkers = [(i, a) for i, a in enumerate(notations) if isinstance(a, MathArg) and len(a.value) > 1]
        first = argmarkers[0][0]
        last = argmarkers[-1][0]

        # all markers should belong to the same (sequence) argument
        assert len(set(am[1].value[0] for am in argmarkers)) == 1

        separator: Optional[list[MAst]] = None
        if len(argmarkers) > 1:
            second = argmarkers[1][0]
            separator = notations[first+1:second]

        notations = notations[:first] + [MathSeqArg(notations[first].value[0], separator)] + notations[last+1:]

    return notations, args


def gf_xml_math_to_mast(node: GfXmlNode) -> MAst:
    match node:
        case XmlText(text):
            return MT(text)
        case XmlNode('mrow', children) as x if x.attrs.get('data-ftml-term') in {'OMA', 'OMV'}:
            notations, args = process_math_sem_node(children)
            # sort and group args (quick hack; lacks robustness and error checks)
            args.sort(key=lambda x: (int(x[0][0]), int(x[0][1:] or '0')))
            args2 = []
            for no, arg in args:
                if len(no) == 1: # single argument, no grouping needed
                    args2.append(arg)
                elif no[1:] == '1': # start new group
                    args2.append(MSeq(no[0], [arg]))
                else: # continue group
                    args2[-1].add_arg(arg)  # type: ignore
            return M(
                x.attrs['data-ftml-head'],
                args2,
                notations
            )
        case XmlNode(tag, children) as x:
            # an informal math node
            return MI(tag, [gf_xml_math_to_mast(child) for child in children], x.attrs)
        case _:
            raise ValueError(f"Unexpected node type in math: {type(node)}")


def gf_xml_to_mast(node: GfXmlNode) -> MAst:
    match node:
        case GfNode(value, children):
            return G(value, [gf_xml_to_mast(child) for child in children])
        case XmlNode('math') as m:
            if len(m.children) == 1 and isinstance(m.children[0], XmlNode) and m.children[0].tag == 'mrow' and not m.children[0].attrs:
                # swallow bare mrow
                m = m.children[0]
            assert m.wrapfun
            return Formula([gf_xml_math_to_mast(child) for child in m.children], m.wrapfun)
        case XmlNode(tag, children, attrs, wrapfun) as x:
            for anno in _ANNOS:
                if r := anno.try_from_gfxml(x):
                    return r
            return X(tag, [gf_xml_to_mast(child) for child in children], attrs, wrapfun)
        case _:
            raise ValueError(f"Unexpected node type: {type(node)}")


def mast_to_gfxml(node: MAst, args: Optional[dict[str, MAst]] = None) -> GfXmlNode:
    # args is a dict if we are currently in the instantiation of an M node
    match node:
        case G(value, children):
            return GfNode(value, [mast_to_gfxml(child, args) for child in children])
        case X(tag, children) as x:
            return XmlNode(tag, [mast_to_gfxml(child, args) for child in children], x.attrs, x.wrapfun)
        case Formula(children) as f:
            return XmlNode(
                'math',
                [XmlNode('mrow', [mast_to_gfxml(child, args) for child in children])],
                wrapfun=f.wrapfun
            )
        case MI(value, children) as m:
            return XmlNode(
                value,
                [mast_to_gfxml(child, args) for child in children],
                m.attrs,
            )
        case MT(value):
            return XmlText(value)
        case M(value, children) as m:
            new_args = {str(i): child for i, child in enumerate(children, start=1)}
            return XmlNode(
                'mrow',
                [mast_to_gfxml(child, new_args) for child in m.notation_pattern],
                attrs={'data-ftml-head': value, 'data-ftml-term': 'OMA'},
            )
        case MathArg(value):
            if args is None or value not in args:
                raise ValueError(f"Missing argument for MathArg: {value}")
            return mast_to_gfxml(args[value], None)
        case MathSeqArg(value) as msa:
            if args is None or value not in args:
                raise ValueError(f"Missing argument for MathArg: {value}")
            arg = args[value]
            assert isinstance(arg, MSeq)
            if len(arg.children) > 1:
                assert msa.separator is not None, f"Expected separator for MathSeqArg {value} with multiple children"
            updated_children: list[MAst] = []
            for i in range(len(arg.children)):
                if i > 0 and msa.separator:
                    updated_children.append(deepcopy(msa.separator.clone()))
                updated_children.append(arg.children[i])
            return XmlNode(
                'mrow',
                [mast_to_gfxml(child, None) for child in updated_children],
                attrs={'data-ftml-arg': value},
            )
        case S() as s:
            return s.to_gfxml()
        case _:
            raise ValueError(f"Unexpected node type: {type(node)}")