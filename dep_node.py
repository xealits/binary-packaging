'''
whatever is needed to handle dependency graphs
'''

from collections import namedtuple


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
        # case of a cycle in the graph
        if self in prefix_list:
            #yield prefix_self
            yield prefix_list + [self]

        else:
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

DepDefinition = namedtuple('DepDefinition', 'filename version hash')

class DepNode(GraphNode):
    '''
    A specialised graph for dependency nodes.
    The node represents a dpendency in abstract, not a concrete full path.
    TODO: try it out and see whether it makes sense.
    '''

    def __init__(self, filename, soname, full_definition, full_path='', rpath='', needed=set()):
        assert filename == full_definition.filename
        self.full_definition = full_definition

        value = {'full_definition': full_definition,
               'soname': soname,
               'rpath': rpath,
               'full_path': full_path}

        super().__init__(filename, value, children=needed)

        for dep in needed:
            dep.parents.add(self) # TODO: check, it has to add the node and resolve conflicts

    def __hash__(self):
        return hash((self.name, self.value['full_definition']))

    def fname_conflict(self, other_dep):
        '''
        same file name - same file in the dependency directory.
        Either re-use the same file for both dependencies,
        or resolve the version conflict.
        '''
        return self.full_definition.filename == other_dep.full_definition.filename

    def version_conflict(self, other_dep):
        '''
        '''
        return self.full_definition.version != other_dep.full_definition.version
        # TODO: support version ranges, use some module for semantic versions

    def hash_conflict(self, other_dep):
        '''
        '''
        self_hashes  = self.full_definition.hash
        other_hashes = other_dep.full_definition.hash
        # supports sets of hashes
        assert isinstance(self_hashes, frozenset) and isinstance(other_hashes, frozenset)

        # if any of the hash sets is empty - no conflict
        if len(self_hashes) == 0 or len(other_hashes) == 0:
            return False

        return len(self_hashes and other_hashes) == 0

    def no_conflict(self, other_dep):
        if not fname_conflict(other_dep):
            return True

        # file names are the same - check whether they collide
        if not version_conflict(other_dep):
            return True

        # TODO oneline this logic?
        if not hash_conflict(other_dep):
            return True

        return False

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


