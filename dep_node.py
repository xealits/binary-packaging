'''
whatever is needed to handle dependency graphs
'''

from collections import namedtuple
import logging


class GraphNode:
    '''
    a class for dependency graphs
    a modified clone of OptNode from curses_menu
    '''

    def __init__(self, name, value=None, children=set(), parents=set(), logger=None):
        self.name = str(name) # TODO: not sure if name is always str
        self.value = value
        self.children = children
        self.parents  = parents

        # confirm that the input children and parents are sets
        for set_param in (self.children, self.parents):
            assert(isinstance(set_param, set))

            # check that all children are GraphNode
            for item in set_param:
                assert isinstance(item, GraphNode)

    def __hash__(self):
        return hash((self.name, self.value))

    def __repr__(self):
        return f'GraphNode({repr(self.name)}, {repr(self.value)}, {repr(self.children)}, {repr(self.parents)})'

    def __str__(self):
        if self.value is not None:
            #return f'{self.name}={self.value}'
            return f'{self.name}'

        else:
            return f'{self.name}'

    def list_graph(self, prefix_list=[]):
        logging.debug(f'list_graph: {self} [{" ".join(str(n) for n in prefix_list)}]')
        # case of a cycle in the graph
        if self in prefix_list:
            logging.debug(f'list_graph: in list {self in prefix_list} {self == prefix_list[0]} {hash(self) == hash(prefix_list[0])}')
            logging.debug(f'list_graph: in list {self == prefix_list[0]} {self.full_definition} {prefix_list[0].full_definition}')
            #yield prefix_self
            yield prefix_list + [self]

        else:
            logging.debug(f'list_graph: NOT in list')
            prefix_self = prefix_list + [self]
            yield prefix_self

            for opt in [c.list_graph(prefix_self) for c in self.children]:
                yield from opt

    def print_flat(self, delimeter='.'):
        #prefix_self = prefix + str(self)
        #print(prefix_self)

        #for n in self.children:
        #    n.print_flat(prefix_self + '.')
        for opt in self.list_graph():
            print(delimeter.join(str(i) for i in opt))

_DepDefinitionTuple = namedtuple('_DepDefinitionTuple', 'filename version hashes')
# definition hashes is a frozenset

class DepDefinition(_DepDefinitionTuple):
    def __init__(self, *args, **kwargs):
        #super().__init__(*args) # why namedtuple does not need arguments?
        super().__init__()
        assert isinstance(self.hashes, frozenset)

    def __hash__(self):
        return hash((self.filename, self.version, self.hashes))

    def __eq__(self, other):
        if not isinstance(other, DepDefinition):
            return False

        return self.eq_fname(other) and \
               self.eq_version(other) and \
               self.eq_hash(other)

    def eq_fname(self, other_dep):
        '''
        same file name - same file in the dependency directory.
        Either re-use the same file for both dependencies,
        or resolve the version conflict.
        '''
        return self.filename == other_dep.filename

    def eq_version(self, other_dep):
        '''
        '''
        # if version strings are empty - it matches any version
        if not self.version or not other_dep.version:
            return True

        return self.version == other_dep.version
        # TODO: support version ranges, use some module for semantic versions

    def eq_hash(self, other_dep):
        '''
        '''
        self_hashes  = self.hashes
        other_hashes = other_dep.hashes
        # supports sets of hashes
        assert isinstance(self_hashes, frozenset) and isinstance(other_hashes, frozenset)

        # if any of the hash sets is empty - no conflict
        if len(self_hashes) == 0 or len(other_hashes) == 0:
            return True

        return len(self_hashes and other_hashes) != 0

    def no_conflict(self, other_dep):
        '''
        matches(self, other_dep)

        Self is a superset of a definition for other_dep.
        Name is the same. The version and the hashes are supersets.
        '''

        # TODO: what if I look for "any" definition in the rules?
        #       the rule cannot be a superset for that, right?
        #       think through how the matching should perform.

        return self.eq_fname(other_dep) and \
               self.eq_version(other_dep) and \
               self.eq_hash(other_dep)

def str_to_def(string):
    name, version, hashstrs = string.split(',')
    if hashstrs:
        hashes = frozenset(hashstrs.split(':'))
    else:
        hashes = frozenset()
    return DepDefinition(name, version, hashes)

class DepNode(GraphNode):
    '''
    A specialised graph for dependency nodes.
    The node represents a dpendency in abstract, not a concrete full path.
    TODO: try it out and see whether it makes sense.
    '''

    def __init__(self, filename, soname, version, full_definition, full_path='', rpath='', needed=set(), parent_nodes=set()):
        assert filename == full_definition.filename
        assert isinstance(full_definition, DepDefinition)
        self.full_definition = full_definition
        self.name = full_definition.filename

        value = {'full_definition': full_definition,
               'soname': soname,
               'version': version,
               'rpath': rpath,
               'full_path': full_path}

        super().__init__(filename, value, children=needed, parents=parent_nodes)

        for dep in needed:
            dep.parents.add(self)
            # TODO: check, it has to add the node and resolve conflicts
            #       can the nodes overwrite each other in the set?
            #       how the set distinguishes them?

    def __hash__(self):
        return hash((self.name, self.value['full_definition']))
        #return super().__hash__()

    def __eq__(self, other):
        if not isinstance(other, DepNode):
            return False

        return self.full_definition == other.full_definition

    def eq_fname(self, other_dep):
        '''
        same file name - same file in the dependency directory.
        Either re-use the same file for both dependencies,
        or resolve the version conflict.
        '''
        return self.full_definition.eq_fname(other_dep.full_definition)

    def eq_version(self, other_dep):
        '''
        '''
        return self.full_definition.eq_version(other_dep.full_definition)

    def eq_hash(self, other_dep):
        '''
        '''
        return self.full_definition.eq_hash(other_dep.full_definition)

    def no_conflict(self, other_dep):
        return self.full_definition.no_conflict(other_dep.full_definition)

"""
I might want to search through the graph
although probably it just should be a separate function

    def match_name(self, substr):
        # TODO: just add full regexp
        match_last = False
        if substr[-1] == '$':
            substr = substr[:-1]
            match_last = True

        if substr not in self.name:
            return False

        match_ind = self.name.index(substr)

        if substr in self.name and match_last and self.name[match_ind:] != substr:
            return False

        self.highlight_name(match_ind, match_ind+len(substr))
        return True

    def match_selector(self, selector):
        '''match_selector(self, selector)

        Returns True or False. Matches the basic selectors:
        = for value
        . for basic type
        the rest is name match
        '''
        assert len(selector) > 0
        if selector[0] in ('=', '.'):
            assert len(selector) > 1

        if selector[0] == '=' and selector[1:] == str(self.value):
            self.highlight_value(True)
            return True

        if selector[0] == '.':
            type_matched = False
            type_matched |= selector[1:] == 'int' and type(self.value) == int
            type_matched |= selector[1:] == 'float' and type(self.value) == float
            type_matched |= selector[1:] == 'str' and type(self.value) == str
            return type_matched

        return self.match_name(selector)

    def match_selectors(self, selectors, prev_nodes=[]):
        '''match_selectors(self, selectors, prev_nodes=[]):

        In general, matching returns an option list from the tree of GraphNode-s.
        Therefore `match_selector` returns True or False whether this node
        matched the selector, and sets the highlights in self node, and in the
        child nodes if needed.

        Special selectors:
        = for value
        . for basic types of value
        > prefix to match child nodes, including [.=]
        '''

        # test and clean up the selectors here
        checked_selectors = []
        for sel in selectors:
            assert len(sel) > 0

            if all(ch in ('>', '=', '.') for ch in sel):
                if logger is not None: # TODO: add a default logger
                    logger.warning(f'got an empty special selector: {sel}')
                continue

            checked_selectors.append(sel)

        # run the recursive matching
        if len(checked_selectors) == 0:
            # done
            for opt in self.list_graph():
                yield prev_nodes + opt

        else:
            yield from self._match_selectors(checked_selectors, prev_nodes)

    def _match_selectors(self, selectors, prev_nodes=[]):
        assert len(selectors) > 0
        #if len(selectors) == 0:
        #    # the all selectors got mathed
        #    for opt in self.list_graph():
        #        #yield prev_nodes + opt
        #        return prev_nodes + opt

        sel = selectors[0]
        assert len(sel) > 0

        ## skip empty special selectors
        ##if sel[0] in ('>', '=', '.') and len(sel) == 1:
        #if all(ch in ('>', '=', '.') for ch in sel):
        #    if logger is not None: # TODO: add a default logger
        #        logger.warning(f'got an empty special selector: {sel}')
        #    selectors = selectors[1:]
        #    sel = selectors[0]
        #    #self.match_selectors(selectors[1:], prev_nodes)

        matched = False
        matched_self = False
        if sel[0] == '>':
            # children names
            cnode_selector = sel[1:]

            for c in self.children:
                #yield from c.match_selectors([sel[0][1:]] + selectors[1:], prev_nodes + [self])
                matched |= c.match_selector(cnode_selector)

        else:
            matched = matched_self = self.match_selector(sel)

        next_selectors = selectors[1:] if matched else selectors
        if len(next_selectors) == 0:
            # done
            for opt in self.list_graph():
                yield prev_nodes + opt

        elif matched and not matched_self:
            # matched something in child nodes
            # the matching process stays at this node
            yield from self._match_selectors(next_selectors, prev_nodes)

        else:
            for c in self.children:
                yield from c._match_selectors(next_selectors, prev_nodes + [self])
"""


