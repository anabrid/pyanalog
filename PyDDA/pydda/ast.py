#!/usr/bin/env python3

"""
This module is the heart of the PyDDA code.

It contains a minimalistic pythonic standalone abstract syntax tree
implementation.
"""

# There are no dependencies. All Python included.
import os, sys, textwrap, itertools, pprint, collections, types, builtins
flatten = lambda l: [item for sublist in l for item in sublist]
unique = lambda l: list(set(l))


class Symbol:
    """
    A symbol is similar to a LISP atom which has a Head and a tail,
    where tail is a list. Common notations are
    * head[tail] in Mathematica,
    * (head, tail) in Lisp
    * head(tail) in C-like languages like Python, Perl, Fortran, C
    * Actually [head, *tail] in Python, but we don't use that.
    A symbol also represents a vertex and it's childs in an ordered tree.
    Think of head being the vertex and tail the (edge) list of children.
    We use the Symbol class to represent the abstract syntax tree (AST)
    of the DDA language for describing ODEs and circuitery.
    
    When you call str() or similar on this class, it will print its
    representation in the C-like notation. This notation is identical
    to the "classical" DDA language.
    """
    def __init__(self, head, *tail):
        self.head = head
        self.tail = tail
    def __call__(self, *tail):
        return Symbol(self.head, *tail)
    def __str__(self):
        # could also say tailstr = str(self.tail) if len(self.tail) else ""
        tailstr = "(" + ", ".join(map(str, self.tail)) + ")" if self.tail else ""
        return str(self.head) + tailstr
    def __eq__(self, other):
        "Allow checks Symbol('foo') == Symbol('foo')"
        if isinstance(other, str): raise TypeError(f"Convert the string '{other}' to Symbol before comparing with Symbol {self}.")
        if not isinstance(other, Symbol): raise TypeError(f"{other} is not a Symbol. Cannot compare with {self}.")
        return self.head == other.head and \
               len(self.tail) == len(other.tail) and \
               all([ a == b for a,b in zip(self.tail,other.tail) ])
    def __hash__(self):
        "Allows Symbol to be keys in dictionaries. Also used for persistence"
        return hash(str(self)) # not yet tested, use with care
    
    # Don't repeat yourself:
    __repr__ = __str__
    __unicode__ = __str__
    
    # Here is a bunch of handy methods to deal with Symbols:
    
    def is_variable(self):
        "A variable is a symbol without a tail."
        return len(self.tail) == 0

    def is_term(self):
        "A term is a symbol with a tail."
        return not self.is_variable()

    def variables(self):
        """Compute the dependencies of this symbol, i.e. other variables directly occuring
        in the tail."""
        return [ el for el in self.tail if el.is_variable() ]

    def all_variables(self):
        "Also find variables in all child terms"
        return unique(flatten([ el.all_variables() if el.tail else [el] for el in self.tail if is_symbol(el)]))

    def all_terms(self):
        "Find all terms in all child terms"
        return unique(flatten([ el.all_terms() for el in self.tail if is_symbol(el) and el.tail() ]))

    def map_heads(self, mapping):
        """
        Call a mapping function on all heads in all (nested) subexpressions.
        This is suitable to rename variable names.
        Example:
        > map_heads( Symbol("x", Symbol("y"), 2), lambda x: x+"foo")
        xfoo(yfoo, 2)
        """
        return Symbol(mapping(self.head), *[(el.map_heads(mapping) if is_symbol(el) else el) for el in self.tail])

    def map_tails(self, mapping):
        return Symbol(self.head, *[(mapping(el.map_tails(mapping)) if is_symbol(el) else el) for el in self.tail])
        
# Convenience functions:
def is_symbol(smbl):
    return isinstance(smbl, Symbol)

#def convenience(method, cls=Symbol):
#    def fun(inst):
#        if not isinstance(inst, cls): raise ValueError(f"'{str(inst)}' is of type {type(inst)} but {str(cls)} required")
#        return getattr(inst, method)
#    return fun
#map_heads = convenience("map_heads")

def symbols(*query):
    """
    Quickly make symbol objects. Usage similar to sympy's symbol function:
    > a, b = symbol("a", "b")
    > x, y, z = symbol("x, y, z")
    """
    symbols = [ Symbol(p.strip()) for q in query for p in q.split(",") ]
    return symbols if len(symbols)>1 else symbols[0]


def topological_sort(dependency_pairs):
    'Sort values subject to dependency constraints'
    # stolen: https://stackoverflow.com/a/42359401
    num_heads = collections.defaultdict(lambda: 0)   # num arrows pointing in
    tails = collections.defaultdict(list)      # list of arrows going out
    heads = []                     # unique list of heads in order first seen
    for h, t in dependency_pairs:
        num_heads[t] += 1
        if h in tails:
            tails[h].append(t)
        else:
            tails[h] = [t]
            heads.append(h)

    ordered = [h for h in heads if h not in num_heads]
    for h in ordered:
        for t in tails[h]:
            num_heads[t] -= 1
            if not num_heads[t]:
                ordered.append(t)
    cyclic = [n for n, heads in num_heads.items() if heads]
    Results = collections.namedtuple('topological_sort', ['sorted', 'cyclic'])
    ordered, cyclic = ordered[::-1], cyclic[::-1] # I find reverse logic more logical
    return Results(ordered, cyclic)

class State(collections.UserDict):
    """
    A state is a dictionary which is by convention a mapping from variable
    names (as strings) to their symbolic meaning, i.e. a Symbol(). Since
    Symbol() spawns an AST, a state is a list of variable definitions.

    A state holds the content of a DDA file.
    
    This class collects a number of basic helper routines for dealing with
    states.
    
    In order to simplify writing DDA files in python, this class extends
    the dictionary idiom with the following optional features, which
    are turned on by default:
    
    * Type peacemaking: Query a Symbol(), get translated to str().
      Example: State(foo=Symbol("bar"))[Symbol("foo")] == Symbol("bar")
    * Default Symbol: Automatically add an entry when unknown.
      Example: State()["foo"] == Symbol("foo")
    
    By intention, the keys of the State are always strings, never Symbols.
    This also should make sure you don't use complex ASTs for keys,
    such as Symbol("foo", "bar").
    
    As this is a collections.UserDict, you can access the underlying
    dict by accessing the attribute State().data
    """    
    def __init__(self, initialdata=dict(), type_peacemaking=True, default_symbol=True):
        self.type_peacemaking = type_peacemaking
        self.default_symbol = default_symbol
        super().__init__(initialdata)

    def __getitem__(self, name):
        if self.type_peacemaking and isinstance(name, Symbol):
            name = name.head
        if self.default_symbol and not name in self.data:
            self.data[name] = Symbol(name)
        return super().__getitem__(name) # or just self.data[name] 
    
    def __setitem__(self, name, value):
        if self.type_peacemaking and isinstance(name, Symbol):
            name = name.head
        return super().__setitem__(name, value)
            
    def update(self, other_dict):
        if isinstance(other_dict, State):
            other_dict = other_dict.data
        return super().update(other_dict) # always returns None!
    
    def __repr__(self):
        return "{}({})".format(type(self).__name__, pprint.pformat(self.data))
        
    # Actual useful methods come here:
    
    def equation_adder(self):
        """
        Syntactic sugar for adding new equations to the system.
        Usage:
        > eq = state.equation_adder
        > eq(y=int(x))
        > eq(x=add(y,z), z=int(x,0,0.1))
        
        Known limitations: This doesn't work because keywords must
        not be variables:        
        > x,y,z = State("x,y,z")
        > eq(x=add(y,z))
        """
        def adder(**dct):
            for k,v in dct.items():
                self[k] = v
        return adder
        
    def map_tails(self, mapper):
        apply_mapper = lambda el: el.map_tails(mapper) if el.is_term() else mapper(el)
        return State({var: apply_mapper(self[var]) for var in self })
    
    def map_heads(self, mapper):
        """
        This function is suitable for renaming variables.
        mapper is always executed on the string variable names (Symbol heads)
        """
        return State({ mapper(var): self[var].map_heads(mapper) for var in self })
    
    def symbols(self, *query):
        "Same as symbols() above, but register at self (state)"
        return [ self[x.head] for x in symbols(*query) ]
    
    def constant_validity(self):
        """
        Check validity of numeric constants in the state.
        Depending on context, values -1 < t < +1 are illegal.
        """
    
    def dependency_graph(self):
        # Comptue adjacency list of dependencies. All is strings, no more symbols
        adjacency_list = { k: list(map(str, self[k].all_variables())) for k in self }
        # Edge list
        edge_list = [ (k,e) for k,dep in adjacency_list.items() for e in dep ]
        return edge_list
    
        # We can call topological_sort() on the result of this method.
        
    def draw_dependency_graph(self, export_dot=True, dot_filename="test.dot"):
        """
        If you have networkx and pyGraphViz installed, you can use this method
        to draw the dependency graph with Dot/GraphViz.
        Your distribution package python-graphviz is probably not pygraphviz.
        You are on the safe side if you run: pip install pygraphviz
        """
        import networkx as nx
        from networkx.drawing.nx_agraph import graphviz_layout
        
        G = nx.DiGraph()
        G.add_edges_from(self.dependency_graph())
        if export_dot:
            nx.nx_agraph.write_dot(G, dot_filename)
            print(f"Exported to {dot_filename}. Running dot...")
            os.system(f"dot -Tpng {dot_filename} > {dot_filename}.png && open {dot_filename}.png")
        return G

    def name_computing_elements(self):
        """
        Name all computing elements / intermediate expressions.
        Limitations: expresions like foo(bar, baz(bla)) are not resolved.
        This is good for const(1) but bad for neg(foo) or sqrt(bar).
        """
        symbol_counter = collections.defaultdict(lambda:0)
        intermediates = {}
        #NamedSymbol = collections.namedtuple('NamedSymbol', ['symbol', 'number'])
        def register_computing_element(el):
            if len(el.tail) >= 2 and not el in intermediates:
                symbol_counter[el.head] += 1
                named_symbol = "%s_%d" % (el.head, symbol_counter[el.head])
                while named_symbol in self:
                    named_symbol += "_"
                intermediates[named_symbol] = el
                return Symbol(named_symbol)
            return el
        
        linearized_state = self.map_tails(register_computing_element)
        linearized_state.update(intermediates)
        return linearized_state
    

class BreveState(State):
    """
    This subclass of a state adds syntactic sugar by allowing attribute/member access
    notation. Instead of state["foo"] you can write state.foo on instances of
    this class.
    
    Known limitation:
    * Breaks Python class introspection (for instance tab completion in iPython)
    * Of course users cannot add any non-data related attribute (or method)
    
    If you find this class useful, you also might like types.SimpleNamespace or
    collections.collections.namedtuple. Both are basically immutable, while this object type
    is mutable by intention.
    """    
    wellknown = ("data", "type_peacemaking", "default_symbol")
    isinternal = lambda name: (not is_symbol(name)) and (name in BreveState.wellknown or name.startswith("_"))

    def __getattr__(self, name):
        return self.__dict__[name] if BreveState.isinternal(name) else self.__getitem__(name)
    def __setattr__(self, name, value):
        if BreveState.isinternal(name):
            self.__dict__[name] = value
        else:
            self.__setitem__(name, value) # or self.data[name] = value


# The following code has to be cleaned/finished in order to provide a proper CLI.
# That should move to a dedicated package.

def run_cli(argv=sys.argv):
    import argparse # python included
    int = builtins.int # just to go sure
    
    default_compiler = os.getenv("CC", "cc")
    
    parser = argparse.ArgumentParser(description="PyDDA, the AST-based DDA compiler", epilog=__doc__)

    parser.add_argument("circuit_file", help="Contains the DDA setup (traditional file)")
    parser.add_argument("-e", "--export", choices=["C", "DDA", "Dot"], help="File formats which can be generated")
    
    C = parser.add_argument_group(title="Arguments for C++ code generation (Only apply if --export=C)")
    C.add_argument("-N", "--iterations", type=int, help="Number of integration steps to be performed")
    C.add_argument("-m", "--modulus", type=int, help="Output a value every <modulus> iteration steps")
    C.add_argument("-v", "--variables", nargs="*", help="List of variables to be plotted (comma seperated)")
    
    C.add_argument("-c", "--compile", action="store_true", help="Compile generated code (using CC environment variable as compiler or defaults to cc)")
    C.add_argument("-r", "--run", action="store_true", help="Run generated code ...")
    
    res = parser.parse_args(argv)
    print(res)
    
    ### TODO: Continue here with actions
    
    
if __name__ == "__main__":
    run_cli()
