#!/usr/bin/env python3
#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the DDA module of the PyAnalog toolkit.
#
# ANABRID_BEGIN_LICENSE:GPL
# ANABRID_END_LICENSE
#

"""
The minimalistic pythonic standalone abstract syntax tree (**AST**)
representation in this module is the heart of the PyDDA package.
The code has no external dependencies, especially it does not rely
on a Computer Algebra System or even on SymPy.

The :class:`Symbol` object represents a node in a AST and the edges
to it's children. In order to simplify mass symbol generation,
:meth:`symbols` can be used.

The :class:`State` object represents a list (set) of equations.
It basically maps variables to their expressions. The :class:`State`
represents a (traditional) DDA file. From a python perspective, a
:class:`State` is not much more then a dictionary on stereoids.
"""

# all "batteries included":
import os, sys, pprint, collections, types
flatten = lambda l: [item for sublist in l for item in sublist]
unique = lambda l: list(set(l))


class Symbol:
    """
    A symbol is similar to a LISP atom which has a Head and a tail,
    where tail is a list. Common notations for such a type are
    
    * ``head[tail]`` in Mathematica,
    * ``(head, tail)`` in Lisp
    * ``head(tail)`` in C-like languages like Python, Perl, Fortran, C
    * Actually ``[head, *tail]`` in Python, but we don't use that.
      
    A symbol also represents a vertex (node) and it's childs in an ordered tree.
    Think of head being the vertex and tail the (edge) list of children.
    We use the Symbol class to represent the abstract syntax tree (AST)
    of the DDA language for describing ODEs and circuitery.
    
    When you call ``str()`` or similar on instances of this class, it will
    print its representation in the C-like notation. This notation is
    identical to the "classical" DDA language.
    
    There are two types of Symbols: **Variables** have no tail, they just
    consist of a head:
    
    >>> x = Symbol("x")
    >>> print(x)
    x
    >>> x.head
    'x'
    >>> x.tail
    ()
    
    In contrast, **Terms** have a tail:
    
    >>> f = Symbol("f", Symbol("x"), Symbol("y"))
    >>> print(f)
    f(x, y)
    >>> f.head
    'f'
    >>> f.tail
    (x, y)
    
    Variables can be used to create complex expressions for which
    they then serve for as a head:
    
    >>> f,x,y,z = Symbol("f"), Symbol("x"), Symbol("y"), Symbol("z")
    >>> f(x,y)
    f(x, y)
    >>> # example for kind of nonsensical terms:
    >>> x(x,f,x)
    x(x, f, x)
    
    Calling a symbol will always replace it's tail:
    
    >>> f(x)(y)
    f(y)
    
    Symbols are equal to each other if their head and tail equals:
    
    >>> a1, a2 = Symbol("a"), Symbol("a")
    >>> a1 == a2
    True
    >>> f(x) == f(x)
    True
    >>> f(x) == f(x,x)
    False
    
    Symbols can be used as dictionary keys, since they hash trivially
    due to their unique canonical (pythonic) string interpretation.
    
    .. note::
    
       In order to avoid confusion between Python Strings and Symbols,
       you should
       
       - *always* use strings as Symbol heads but
       - *never* use strings in Symbol tails. Instead, use there Symbols
         only.
       
       Think of Symbol implementing the following type (hint):
       ``Tuple[str, List[Symbol]]``.
       
       In the above example, you can write
       
       >>> f = Symbol("f", "x", "y")
       >>> print(f)
       f(x, y)
       
       which looks identical to the example given before. This is
       *by intention* and breaks Python standard for ``repr()``
       behaviour. It can be hard to find such errors. That could probably
       be improved by providing the correct ``repr()``.
       
       It is a good convention to *only* have Symbols and floats/integers
       being part of the AST.
    
    
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
        "Allow to check Symbol('foo') == Symbol('foo')"
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
        """Compute the direct dependencies of this symbol, i.e. other variables
        directly occuring in the tail."""
        return [ el for el in self.tail if el.is_variable() ]

    def all_variables(self):
        "Like :meth:variables, but also find variables in all children."
        return unique(flatten([ el.all_variables() if el.tail else [el] for el in self.tail if is_symbol(el)]))

    def all_terms(self):
        "Like :meth:all_variables, but for terms: Returns a list of all terms in all children of this node."
        return unique(flatten([ el.all_terms() for el in self.tail if is_symbol(el) and el.tail() ]))

    def map_heads(self, mapping):
        """
        Call a mapping function on all heads in all (nested) subexpressions.
        Returns a new mapped Symbol. This routine is suitable for renaming
        variable names within the AST. Example usage:

        >>> Symbol("x", Symbol("y"), 2).map_heads(lambda head: head+"foo")
        xfoo(yfoo, 2)
        """
        return Symbol(mapping(self.head), *[(el.map_heads(mapping) if is_symbol(el) else el) for el in self.tail])

    def map_tails(self, mapping):
        """
        Calls a mapping function on all tails in all (nested) subexpressions.
        Returns a new mapped Symbol.
        """
        return Symbol(self.head, *[(mapping(el.map_tails(mapping)) if is_symbol(el) else el) for el in self.tail])
    
    def draw_graph(self, graph=None):
        """
        Uses graphviz to draw the AST down from this symbol.
        
        See also :method:`State.draw_dependency_graph` for similar draph
        drawing code and notes on python library dependencies.
        
        >>> x,y,z = symbols("x,y,z")
        >>> expression = x(1,y,2,z(3,4))
        >>> graph = expression.draw_graph()
        >>> print(graph)  # doctest: +NORMALIZE_WHITESPACE
        digraph "DDA-Symbol" {
           size="8,5"
           node [shape=doublecircle]
           x
           node [shape=circle]
           x -> 1
           node [shape=doublecircle]
           y
           node [shape=circle]
           x -> y
           x -> 2
           node [shape=doublecircle]
           z
           node [shape=circle]
           z -> 3
           z -> 4
           x -> z
        }
        >>> graph.view() # Call this to draw the graph  # doctest: +SKIP
        """
        if not graph:
            from graphviz import Digraph
            graph = Digraph("DDA-Symbol", filename="symbol.gv")
            graph.attr(size="8,5")  # rankdir="LR"
        
        graph.attr("node", shape="doublecircle")
        graph.node(self.head)
        
        graph.attr("node", shape="circle")
        for k in self.tail:
            if is_symbol(k):
                graph = k.draw_graph(graph)
                graph.edge(self.head, k.head)
            else:
                graph.edge(self.head, str(k))

        return graph

def is_symbol(smbl):
    "Convenience function"
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
    
    >>> a, b = symbols("a", "b")
    >>> x, y, z = symbols("x, y, z")
    """
    symbols = [ Symbol(p.strip()) for q in query for p in q.split(",") ]
    return symbols if len(symbols)>1 else symbols[0]

def topological_sort(dependency_pairs):
    """Sort a graph (given as edge list) subject to dependency constraints.
    The result are two lists: One for the sorted nodes, one for the
    unsortable (cyclically dependent) nodes.
    
    Implementation shamelessly stolen from https://stackoverflow.com/a/42359401
    """
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
    names (as *strings*) to their symbolic meaning, i.e. a ``Symbol()``.
    We refer to the keys in the dictionary as the *Left Hand Side* (LHS) and
    the values in the dictionary as the *Right Hand Side* (RHS), in analogy
    to an Equation.

    .. note::

       Since ``Symbol()`` spawns an AST, a state is a list of variable definitions.    
       A DDA file is a collection of equations. Therefore, a state holds the
       content of a DDA file.
   
    This class collects a number of basic helper routines for dealing with
    states.
    
    In order to simplify writing DDA files in Python, this class extends
    the dictionary idiom with the following optional features, which
    are turned on by default:
    
    - **Type peacemaking**: Query a ``Symbol()``, get translated to
      ``str()``:
      
      >>> State({ "foo": Symbol("bar")})[Symbol("foo")] == Symbol("bar")
      True
      
    - **Default Symbol**: Automatically add an entry when unknown:
      
      >>> State()["foo"] == Symbol("foo")
      True
    
    .. note::
    
       By intention, the keys of the State are always strings, never Symbols.
       This also should make sure you don't use complex ASTs for keys,
       such as ``Symbol("foo", "bar")``.
    
    As this is a ``collections.UserDict``, you can access the underlying dict:
    
    >>> x,y = symbols("x,y")
    >>> add, integrate = symbols("add", "integrate")
    >>> eqs = { x: add(y,y), y: integrate(x) }
    >>> state = State(eqs); print(state)
    State({'x': add(y, y), 'y': integrate(x)})
    >>> state.data
    {'x': add(y, y), 'y': integrate(x)}

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
        Syntactic sugar for adding new equations to the system. Usage:

        >>> state = State()
        >>> x,y,z,add,int = symbols("x,y,z,add,int")
        >>> eq = state.equation_adder()
        >>> eq(y=int(x))
        >>> eq(x=add(y,z), z=int(x,0,0.1))
        >>> state
        State({'x': add(y, z), 'y': int(x), 'z': int(x, 0, 0.1)})
        
        Known limitations: This doesn't work any better then the ``BreveState``
        below because keywords must not be variables, they will always resolve
        to their string representation.
        
        >>> foo = Symbol("bar")
        >>> s1, s2 = State(), State()
        >>> eq1 = s1.equation_adder()
        >>> eq1(foo=42)
        >>> s2[foo] = 42
        >>> s1
        State({'foo': 42})
        >>> s2
        State({'bar': 42})
        """
        def adder(**dct):
            for k,v in dct.items():
                self[k] = v
        return adder
        
    def map_tails(self, mapper):
        "Apply :meth:`Symbol.map_tails` on all right hand sides."
        apply_mapper = lambda el: el.map_tails(mapper) if el.is_term() else mapper(el)
        return State({var: apply_mapper(self[var]) for var in self })
    
    def map_heads(self, mapper):
        """
        This function is suitable for renaming variables.
        mapper is always executed on the string variable names (Symbol heads)
        """
        return State({ mapper(var): self[var].map_heads(mapper) for var in self })
    
    def symbols(self, *query):
        "Same as :meth:`symbols()` above, but register at self (state)"
        return [ self[x.head] for x in symbols(*query) ]
        
    def constant_validity(self):
        """
        Check validity of numeric constants in the state.
        Depending on context, values -1 < t < +1 are illegal.
        
        (Not yet implemented!)
        """
        pass # TBD, probably not here
    
    def dependency_graph(self):
        """Returns the edge list of the variable dependency graph of this state.
        We can call :meth:`topological_sort()` on the result of this method.
        """
        # Comptue adjacency list of dependencies. All is strings, no more symbols
        adjacency_list = { k: list(map(str, self[k].all_variables())) for k in self }
        # Edge list
        edge_list = [ (k,e) for k,dep in adjacency_list.items() for e in dep ]
        return edge_list
        
    def draw_dependency_graph(self, export_dot=True, dot_filename="test.dot"):
        """
        If you have ``networkx`` and ``pyGraphViz`` installed, you can use this method
        to draw the *variable dependency graph* (see method :meth:`dependency_graph()`)
        with ``Dot``/``GraphViz``. This method will return the ``nx.DiGraph()`` instance.
        If ``export_dot`` is set, it will also write a dotfile, call ``dot`` to
        render it to a bitmap and open that bitmap.
        
        .. note::
        
           Your distribution package ``python-graphviz`` is probably not ``pygraphviz``.
           You are on the safe side if you run: ``pip install pygraphviz``
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
        Name all computing elements / intermediate expressions. Returns
        a new State which is *linearized* in a way that the numbering proposes a computing
        order.
        
        Linearization is a fix point operation, i.e. for any
        ``lin = state.name_computing_elements()`` it is ``lin == lin.name_computing_elements()``.
        
        .. warning::
           
           Known limitations: expresions like ``foo(bar, baz(bla))`` are not resolved.
           This is good for ``const(1)`` but bad for ``neg(foo)`` or ``sqrt(bar)``:
           
           >>> x,y = symbols("x,y")
           >>> ns = State({ x: x(x, x(y)) })
           >>> ns.name_computing_elements() == ns
           True
           
           But this is clearly wrong, the correct linearization would give ``x(y)`` a name.
           FIXME (https://lab.analogparadigm.com/koeppel/dda/-/issues/8)
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
        
    def variable_ordering(self):
        """
        Will perform an analysis of all variables occuring in this state (especially in the RHS).
        This is based on the linarized variant of this state (see :meth:`name_computing_elements()`).
        
        The return value is an object (actually a types.SimpleNamespace instance) which contains
        lists of variable names (as strings). The properties (categories) are primarly
        
          * explicit constants: Any entry ``state["foo"] = const(1.234)``
          * State variables/evolved variables: Any outcome of a time integration, i.e. ``int(...)``,
            i.e. ``Symbol("int")``. This can be as simple as ``state["foo"] = int(Symbol("foo"),...)``.
            Complex terms such as ``state["foo"] = mult(int(foo), int(bar))`` will result in
            intermediate variables called like ``int_0``, ``int_1``(see ``name_computing_elements()``
            for the code which invents these names), which are the actual evolved variables.
          * Auxilliary variables: Any other variables which are required to compute evolved
            variables.
            
        By intention, we **sort only the aux. variables**. One should check that they DO NOT have any
        cyclic dependency, because feedback loops are only useful on integrators at this level
        of circuit modeling.

        We differntiate the auxilliaries further into:
        
          * ``sorted_aux_vars``: Auxilliaries required to compute the state variable changes
          * ``cyclic_aux_vars``: Auxilliaries which have a cyclic dependency on each other
            (this should not happen as it won't lead to a stable circuit)
          * ``unneeded_auxers``: Auxilliaries which are not required to compute the state.
            These are probably used in postprocessing. If they depend on the state variables,
            further work is neccessary.
            
        An imperative code for evolving this state in time should then compute all aux.
        variables in the respective order before computing ``dqdt``. The dependency is
        basically, in pseudo code:
        
        >>> aux  = function_of(aux, state)                    # doctest: +SKIP
        >>> dqdt = function_of(aux, state)                    # doctest: +SKIP
        
        and in the numerical integration schema step
        
        >>> state = function_of(dqdt)                         # doctest: +SKIP
        
        TODO: Write more documentation :-)
        """
        
        lin = self.name_computing_elements()
        vars = types.SimpleNamespace()
        vars.aux = types.SimpleNamespace()
        
        # Thanks to named computing elements, can find all int(...) expressions
        # without searching, since they must come first.
        vars.evolved  = sorted(filter(lambda var: lin[var].head == "int",   lin))
        vars.explicit_constants = sorted(filter(lambda var: lin[var].head == "const", lin))

        # Then compute ALL aux variables BEFORE computing dqdt.
        # The order of dqdt should not be touched, as there CAN NOT be any
        # dependency, since dqdt.foo = int(lin).

        vars.all = sorted(set.union(*[set(map(str, lin[k].all_variables())) for k in self], set(self)))
        vars.aux.all = [ v for v in vars.all if not v in vars.evolved and not v in vars.explicit_constants  ]

        # Linearize aux expressions by dependency sorting.
        dep_edge_list = lin.dependency_graph()
        # Edge direction: (a,b) = [dependent variable a]--[depends on]-->[dependency b]
        aux_dep_edges = [ (a,b) for a,b in dep_edge_list if a in vars.aux.all and b in vars.aux.all ]
        #sorted_vars, cyclic_vars = topological_sort(dep_edge_list)
        vars.aux.sorted, vars.aux.cyclic = topological_sort(aux_dep_edges)

        vars.aux.unneeded = set(vars.aux.all) - (set(vars.aux.sorted) | set(vars.aux.cyclic) | set(vars.explicit_constants))
        
        ordering = ["vars.explicit_constants", "vars.aux.sorted", "vars.aux.cyclic", "vars.evolved", "vars.aux.unneeded"]
        vars.ordering = collections.OrderedDict([ (name, eval(name, {"vars":vars})) for name in ordering ])
        
        return vars

    def export(self, to, **passed_args):
        "Syntactic sugar for dda.export(), for convenience"
        from . import export
        return export(self, to, **passed_args)

class BreveState(State):
    """
    This subclass of a state adds *syntactic sugar* by allowing attribute/member access
    notation. Instead of ``state["foo"]`` you can write ``state.foo`` on instances of
    this class. Example usage:
    
    >>> x,y,z = symbols("x,y,z")
    >>> state = BreveState()
    >>> state.x = x(y,z)
    >>> state.y = y(x,z)
    >>> state.z = z(x,y)
    >>> print(state)
    BreveState({'x': x(y, z), 'y': y(x, z), 'z': z(x, y)})
    
    .. warning::
       
       Known limitations:
    
       * Breaks Python class introspection (for instance tab completion in *iPython*)
       * Of course users cannot add any non-data related attribute (or method)

    See also :meth:`State.equation_adder()` for similar sugar which might have
    unexpected effects:
    
    >>> s, b = State(), BreveState()
    >>> foo = Symbol("bar") # in this context, similar to a string foo = "bar"
    >>> s[foo] = 42         # foo resolves to string represntation "bar"
    >>> b.foo = 42          # equals b["foo"], thus has nothing to do with variable foo
    >>> s
    State({'bar': 42})
    >>> b
    BreveState({'foo': 42})
    
    If you find this class useful, you also might like ``types.SimpleNamespace`` or
    ``collections.namedtuple``. Both are basically immutable, while this object type
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


