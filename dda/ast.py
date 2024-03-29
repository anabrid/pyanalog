#!/usr/bin/env python3
#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the DDA module of the PyAnalog toolkit.
#
# ANABRID_BEGIN_LICENSE:GPL
# Commercial License Usage
# Licensees holding valid commercial anabrid licenses may use this file in
# accordance with the commercial license agreement provided with the
# Software or, alternatively, in accordance with the terms contained in
# a written agreement between you and Anabrid GmbH. For licensing terms
# and conditions see https://www.anabrid.com/licensing. For further
# information use the contact form at https://www.anabrid.com/contact.
# 
# GNU General Public License Usage
# Alternatively, this file may be used under the terms of the GNU 
# General Public License version 3 as published by the Free Software
# Foundation and appearing in the file LICENSE.GPL3 included in the
# packaging of this file. Please review the following information to
# ensure the GNU General Public License version 3 requirements
# will be met: https://www.gnu.org/licenses/gpl-3.0.html.
# For Germany, additional rules exist. Please consult /LICENSE.DE
# for further agreements.
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
import os, sys, pprint, collections, types, warnings, itertools
identity = lambda x:x
flatten = lambda l: [item for sublist in l for item in sublist]
unique = lambda l: list(set(l))

#class VariableTaxonomy(types.SimpleNamespace):
#    """
#    Inherits __init__, __repr__ and __eq__ from the SimpleNamespace.
#    """
#    def __repr__(self):
#        items = ((f"{k}={v!r}" if len(v)<5 else "%s={%s}"%(k,f"{len(v)} items")) for k,v in self.__dict__.items())
#        return f"VariableTaxonomy({', '.join(items)})"
#    def verbose(self):
#        "Calls the 'traditional' full dump of the namespace object"
#        return types.SimpleNamespace.__repr__(self)
#    def __init__(self, **kwargs):
#        super(**kwargs)
#    def find(self,variable):
#        candidates = [ cls for cls, members in self.__dict__.items() if variable in members ]
#        if len(candidates) == 1: return candidates[0]
#        elif len(candidates) > 1:  raise KeyError(f"Variable {variable} is in multiple classes: {candidates}")
#        else: raise KeyError(f"Variable {variable} is in no class.")
#    __contains__ = find
#    def __len__(self): return len(self.__dict__)
#    def where_is(self, variable_list=[]):
#        if not variable_list:
#            variable_list = [ var for var in members for cls,members in self.__dict__.items() ]
#        return { var: self.find(var) for var in variable_list }
#        
    

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
       
       The DDA code helps you to follow this guide. For instance, the
       representation of ``f1`` shows that it is a symbol with two
       string arguments, while ``f2`` has symbol arguments:

       >>> f1 = Symbol("f", "x", "y")
       >>> f2 = Symbol("f", Symbol("x"), Symbol("y"))
       >>> f1
       f('x', 'y')
       >>> f2
       f(x, y)
       
       And DDA prevents you from shooting in your foot:
       
       >>> f, x, y = symbols("f,x,y")
       >>> f3 = Symbol(f,x,y)
       Traceback (most recent call last):
       ...
       TypeError: Trying to initialize Symbol f(x, y) but head f is a Symbol, not a String.
       
       In previous versions of DDA, the thin line between strings and
       symbols hasn't been made so clear and tracing errors was harder.
       
       Summing up, it is a good convention to *only* have Symbols and
       floats/integers being part of the Symbol tails.
    
    """
    def __init__(self, head, *tail):
        self.head = head
        self.tail = tail
        if isinstance(self.head, Symbol):
            raise TypeError(f"Trying to initialize Symbol {self} but head {head} is a Symbol, not a String.")
    def __call__(self, *tail):
        return Symbol(self.head, *tail)
    def __str__(self):
        # could also say tailstr = str(self.tail) if len(self.tail) else ""
        tailstr = "(" + ", ".join(map(repr, self.tail)) + ")" if self.tail else ""
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
        The mapping is effectively carried out on the head (ie. maps strings)
        Returns a new mapped Symbol. This routine is suitable for renaming
        variables and terms within an AST. Example usage:
        
        >>> Symbol("x", Symbol("y"), 2).map_heads(lambda head: head+"foo")
        xfoo(yfoo, 2)

        The mapping is unaware of the AST context, so you have to distinguish
        between variables and terms yourself if you need to. See also
        :meth:`map_variables` for context-aware head mapping. Compare these
        examples to the ones given for :meth:`map_variables`:

        >>> x, map, y = Symbol("x"), lambda _: "y", Symbol("y")
        >>> x.map_heads(map) == x.map_variables(map)  # == y
        True
        >>> x(x,x).map_heads(map) == y(y,y)
        True
        >>> x(x, x(x)).map_heads(map) == y(y, y(y))
        True
        """
        return Symbol(mapping(self.head), *[(el.map_heads(mapping) if is_symbol(el) else el) for el in self.tail])

    def map_variables(self, mapping, returns_symbol=False):
        """
        Calls a mapping function on all variables within the (nested) subexpressions.
        The mapping is effectively carried out on the head (ie. maps strings). This
        is a mixture between :meth:`map_heads` and :meth:`map_tails`.
        
        Returns a new mapped Symbol. This routine is suitable for renaming
        variables but not terms within the AST. Examples:
        
        >>> x, map, y = Symbol("x"), lambda _: "y", Symbol("y")
        >>> x.map_variables(map) == y
        True
        >>> x(x,x).map_variables(map) == x(y,y)
        True
        >>> x(x, x(x)).map_variables(map) == x(y, x(y))
        True
        
        This function ignores non-symbols as they cannot be variables. This is the same
        as :meth:`map_tails` does and is handy when you have numbers within your expressions:
        
        >>> x = Symbol("x")
        >>> expr = x(123, x(9.1), x, x(x, 0.1, x))
        >>> res1 = expr.map_variables(lambda xx: "y")
        >>> res2 = expr.map_variables(lambda xx: Symbol("y"), returns_symbol=True)
        >>> res1 == res2
        True
        >>> res1
        x(123, x(9.1), y, x(y, 0.1, y))
        
        If you want to use ``map_variables`` to change a variable to a term, and/or if your
        mapping function does not return strings but Symbols, use ``returns_symbol=True``:
        
        >>> Symbol("x").map_variables(lambda x: Symbol("y", 123), returns_symbol=True)
        y(123)
        >>> Symbol("x").map_variables(lambda x: Symbol("y", 123)) # this won't work
        Traceback (most recent call last):
        ...
        TypeError: Trying to initialize Symbol y(123) but head y(123) is a Symbol, not a String.
        """
        return (identity if returns_symbol else Symbol)(mapping(self.head)) if self.is_variable() else \
            Symbol(self.head, *[ (el.map_variables(mapping, returns_symbol=returns_symbol) if is_symbol(el) else el) for el in self.tail ])

    def map_tails(self, mapping, map_root=False):
        """
        Calls a mapping function on all tails in all (nested) subexpressions.
        The mapping is carried out on the tail symbols (ie. maps Symbols).
        Returns a new mapped Symbol. The routine is suitable for AST walking,
        adding/removing stuff in the tails while preserving the root symbol.
        This could also be called ``map_symbols``, c.f. :meth:`map_terms`.
        
        Example for recursively wrapping all function calls:
        
        >>> x,y,z = symbols("x,y,z")
        >>> x(y, z(x), x(y)).map_tails(lambda smb: Symbol("foo")(smb))
        x(foo(y), foo(z(foo(x))), foo(x(foo(y))))
        >>> x(y, z(x), x(y)).map_tails(lambda smb: Symbol("foo")(smb), map_root=True)
        foo(x(foo(y), foo(z(foo(x))), foo(x(foo(y)))))
        
        Example for recursively removing certain unary functions ``z(x)`` for any ``x``:

        >>> remover = lambda head: lambda x: x.tail[0] if isinstance(x,Symbol) and x.head==head else x
        >>> x,y,z = symbols("x,y,z")
        >>> x(y, z(x), x(z(y),x)).map_tails(remover("z"))
        x(y, x, x(y, x))
        
        The argument ``map_root`` decides whether the map is run on the
        root node or not. It will be ``map_root=False`` in any recursive use.
        In former instances of this code, it was always ``map_root=False``.
        Example:
        
        >>> (a, b), flip = symbols("a,b"), lambda smb: b if smb.head==a.head else a
        >>> a(b,a,b).map_tails(flip, map_root=True)
        b
        >>> a(b,a,b).map_tails(flip, map_root=False)
        a(a, b, a)
        
        Note how the ``flip`` function cuts every tail and returns variables only.
        Here is a variant which perserves any tail:
        
        >>> (a, b) = symbols("a,b")
        >>> flipper = lambda smb: (b if smb.head==a.head else a)(*smb.tail)
        >>> a(b,a,b).map_tails(flipper, map_root=True)
        b(a, b, a)
        
        Here is another example which highlights how ``map_tails`` can convert terms to
        variables:
        
        >>> x, map, y = Symbol("x"), lambda _: Symbol("y"), Symbol("y")
        >>> x(x,x).map_tails(map, map_root=False)
        x(y, y)
        >>> x(x,x(x,x)).map_tails(map, map_root=False)
        x(y, y)
        
        For real-life examples, study for instance the source code of :mod:`cpp_exporter` or
        grep any DDA code for ``map_tails``.
        
        See also :meth:`map_heads` and :meth:`map_variables` for variants.
        """
        r = Symbol(self.head, *[(mapping(el.map_tails(mapping, map_root=False)) if is_symbol(el) else el) for el in self.tail])
        return mapping(r) if map_root else r

    
    def map_terms(self, mapping, returns_symbol=False):
        """
        Calls a mapping function on all terms within the (nested) subexpressions.
        The mapping is effectively carried out on the term head (ie. maps strings).
        See :meth:`map_variables` for the similar-minded antoganist as well as
        :meth:`map_heads` and :meth:`map_tails` for more *low level* minded variants.
        
        Returns a new mapped Symbol. This routine is suitable for renaming terms
        but not variables within the AST. Examples:
        
        >>> x, map, y = Symbol("x"), lambda _: "y", Symbol("y")
        >>> x.map_terms(map) == x
        True
        >>> x(x,x).map_terms(map) == y(x,x)
        True
        >>> x(x, x(x)).map_terms(map) == y(x, y(x))
        True
        
        This function ignores non-symbols as they cannot be variables, similar to
        :meth:`map_variables`.
        
        It is basically ``map_terms(map) = map_tails(lambda smb: Symbol(map(smb.head))(smbl.tail) if symb.is_variable() else smb)``.
        
        The argument ``returns_symbol`` allows to discriminate between mapping
        functions which return strings (for symbol heads) or symbols. The later
        allows for manipulating expressions.
        """
        if self.is_variable(): return self
        r = mapping(self.head)
        if not returns_symbol: r = Symbol(r)
        return r(*[ (el.map_terms(mapping) if is_symbol(el) else el) for el in self.tail ])
    
    def draw_graph(self, graph=None):
        """
        Uses graphviz to draw the AST down from this symbol.
        
        See also :method:`State.draw_dependency_graph` for similar draph
        drawing code and notes on python library dependencies.
        
        .. note:: This method constructs the graph by drawing edges between similar
           named symbols. This will *not* represent the abstract syntax tree if
           a single symbol head, regardless of whether variable or term, appears
           twice.
           
           If you want to draw the actual AST with this function, you have to make
           each symbol (head) unique by giving them distinct names.
        
        Simple usage example:
        
        >>> x,y,z = symbols("x,y,z")
        >>> expression = x(1,y,2,z(3,4))
        >>> graph = expression.draw_graph()
        >>> print(graph)  # doctest: +NORMALIZE_WHITESPACE
        digraph "DDA-Symbol" {
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
            #graph.attr(size="8,5")  # rankdir="LR"
        
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
    are turned on by default (but can be disabled by constructor
    arguments ``type_peacemaking`` and ``default_symbol``).
    
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
    
    As ``State``` extends ``collections.UserDict``, you can access the underlying
    dictionary:
    
    >>> x,y = symbols("x,y")
    >>> add, integrate = symbols("add", "integrate")
    >>> eqs = { x: add(y,y), y: integrate(x) }
    >>> state = State(eqs); print(state)
    State({'x': add(y, y), 'y': integrate(x)})
    >>> state.data
    {'x': add(y, y), 'y': integrate(x)}
    
    .. warning::

       Don't be fooled by refering to the state while constructing the state. This
       will end up in overly complex expressions. By rule of thumb, only use
       :class:`Symbols` at the state definition (or in particular on the right hand side).
       For instance, you do want to construct a state like
       
       >>> state = State()
       >>> state["x"] = Symbol("add", Symbol("y"), Symbol("y"))
       >>> state["y"] = Symbol("int", Symbol("x"))
       >>> state
       State({'x': add(y, y), 'y': int(x)})
       
       In contrast, this is most likely not what you want:
       
       >>> state = State()
       >>> state["x"] = Symbol("add", Symbol("y"), Symbol("y"))
       >>> state["y"] = Symbol("int", state["x"])
       >>> state
       State({'x': add(y, y), 'y': int(add(y, y))})
       
       This time, you did not exploit the definition of ``state["x"]`` by referencing
       on DDA level but instead inserted the expression by referencing on Python
       level. This is like *compile-time evaluation* versus *runtime evaluation*,
       when *compile-time* is at python and *runtime* is when evaluating the DDA
       expressions in some time evolution code.
       
       Summing up, the mistake above is to reference to ``state`` while constructing7
       the ``state``. You should not do that. You go best by defining the ``Symbol``
       instances before and then only using them all over the place:
       
       >>> x, y, add, int = symbols("x, y, add, int")
       >>> state = State()
       >>> state[x] = add(y,y)
       >>> state[y] = int(x)
       >>> state
       State({'x': add(y, y), 'y': int(x)})

    .. note::

       Why the name? The class name ``State`` seems arbitrary and quirky, ``System`` may
       be a better choice (given that the class instances hold an equation system).
       However, one could also argue that the class instances hold the definition for
       a system in a particular state. especially, ``State.keys()`` are the state
       variables which undergo a definition by their corresponding ``State.values()``.
       Most CAS do not have a special class for collections of equations. Instead,
       they typically have some *equation* type and equation systems are sets or lists
       of equations. In PyDDA, we don't have an equation type because the DDA domain
       specific language (see :mod:`dsl`) doesn't provide advanced treatments of
       equations but is basically only a lengthy definition of a set of equations,
       which you could understand as a mapping/dictionary data type defining the state
       of the system. That's why `State` is actually an enriched `dict`.

    """    
    def __init__(self, initialdata=dict(), type_peacemaking=True, default_symbol=True):
        self.type_peacemaking = type_peacemaking
        self.default_symbol = default_symbol
        super().__init__(initialdata)
        
    @classmethod
    def from_string(cls, *string_or_list_of_strings):
        "Shorthand for :meth:`.dsl.read_traditional_dda`. Returns new instance."
        from .dsl import read_traditional_dda
        return read_traditional_dda("\n".join(string_or_list_of_strings))
    
    def to_string(self):
        "Shorthand for :meth:`.dsl.to_traditional_dda`. Returns a string (representation)."
        from .dsl import to_traditional_dda
        return to_traditional_dda(self, cleanup=False, prefix=None, suffix=None)

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
        
    def map_tails(self, mapper, map_root=True):
        "Apply :meth:`Symbol.map_tails` on all right hand sides."
        apply_mapper = lambda el: el.map_tails(mapper, map_root=map_root) if el.is_term() else mapper(el)
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
        """
        Returns the edge list of the variable dependency graph of this state.
        We can call :meth:`topological_sort()` on the result of this method.
        
        A weird example including some corner cases:

        >>> s1 = State.from_string("foo = const(0.7)", "bar=mult(bar,baz)", "baz=f(bar)")
        >>> s1.dependency_graph()
        [('bar', 'bar'), ('bar', 'baz'), ('baz', 'bar')]
        
        Another even more weird example which exploits raw value assignment,
        something which is not following the ``foo=call(bar)`` requirement for DDA
        files:
        
        >>> a,b,c,d,f = symbols("a,b,c,d,f")
        >>> s2 = State({ a: f(0.7), b: c(b,b), c: 42, d: c })
        >>> s2.dependency_graph()
        [('b', 'b'), ('d', 'c')]
        
        Note that this function always returns list of tuples of strings. No more
        symbols. See also :meth:`draw_dependency_graph` for a quick way of exporting
        or plotting this graph.
        """
        def dependent(rhs):
            if not isinstance(rhs, Symbol): return []
            if rhs.is_term(): return map(str, rhs.all_variables())
            if rhs.is_variable(): return [str(rhs)]
        # Comptue adjacency list of dependencies. All is strings, no more symbols
        adjacency_list = { k: list(dependent(self[k])) for k in self }
        edge_list = [ (k,e) for k,dep in adjacency_list.items() for e in dep ]
        return sorted(edge_list)
        
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

    def name_computing_elements(self, strict=False):
        """
        Name all computing elements / intermediate expressions. Returns
        a new State which is *linearized* in a way that the numbering proposes a computing
        order.
        
        Linearization is an idempotent operation, i.e. for any
        ``lin = state.name_computing_elements()`` it is ``lin == lin.name_computing_elements()``.
        Mathematically, it is a projection of the state on its linearized one.
        
        Linearization means to define a evaluation order and to give unique names
        to all terms occuring. Note that *all* depends on the strictness (`strict=True` vs.
        the default `strict=False`):
        
        >>> x, y, sum, mult = symbols("x, y, sum, mult")
        >>> ns = State({ x: sum(x,y, sum(y, mult(y,x))), y: mult(x) })
        >>> print(ns.name_computing_elements().to_string())              # doctest: +NORMALIZE_WHITESPACE
        mult_1 = mult(y, x)
        sum_1 = sum(y, mult_1)
        x = sum(x, y, sum_1)
        y = mult(x)
        >>> print(ns.name_computing_elements(strict=True).to_string())   # doctest: +NORMALIZE_WHITESPACE
        mult_1 = mult(y, x)
        mult_2 = mult(x)
        sum_1 = sum(y, mult_1)
        sum_2 = sum(x, y, sum_1)
        x = sum_2
        y = mult_2
        
        Here, *strict* means that really *every* term is labeled, even if this yields in "dumb"
        assignments such as ``x = sum_2``. You want a strict naming when enumerating computing elements,
        while a non-strict naming is preferable for brief evaluation. Also note that
        
        >>> x,const = symbols("x,const")
        >>> State({ x: const(42) }).name_computing_elements(strict=False)
        State({'x': const(42)})
        >>> State({ x: const(42) }).name_computing_elements(strict=True)
        State({'const_1': const(42), 'x': const_1})
        >>> State({ x: const(42) }).name_computing_elements(strict=True).name_computing_elements(strict=True) # doctest:+ELLIPSIS +NORMALIZE_WHITESPACE +SKIP
        /.../ast.py:819: UserWarning: State.named_computing_elements(): While counting const, I notice that  const_1 is already part of the state. Maybe you want to run name_computing_elements(strict=False) for idempotence.
          warnings.warn(...)
        State({'const_1': const_1_, 'const_1_': const(42), 'x': const_1})
        
        On this mini example, one especially sees that idempotence is only given when ``strict=False``. 
        It is ``state.name_computing_elements(True) == state.name_computing_elements(s[0]).name_computing_elements(s[1])....name_computing_elements(s[n])``
        when ``s`` is a boolean array of ``len(s)==n`` and ``sum(s) == 1``, i.e. only one
        occurence of ``strict=True`` and all other ``False``.

        The linearized state only has entries of a *normal form* ``state[f_i] = f(v1,v2,...)``
        for a function (term) ``f`` and some variables ``v_j``. Furthermore note how even
        ``x = sum_2`` in the above example indirects the former assignment of ``x = sum(x,y...)``.
        Again, for any value in the linearized state, the tail only contains variables,
        no terms. This is handy for many things, such as circuit drawing, imperative
        evaluation (in combination with :meth:`variable_ordering`, cf. :mod:`cpp_exporter`)
        and determination of integrands/actual variables. For instance
        
        >>> s = State.from_string("foo = const(0.7)", "baz=mult(bar,bar)", "bar = neg(int(neg(baz), foo, 0.3))")
        >>> s
        State({'bar': neg(int(neg(baz), foo, 0.3)), 'baz': mult(bar, bar), 'foo': const(0.7)})
        >>> print(s.name_computing_elements(strict=True).to_string())    # doctest: +NORMALIZE_WHITESPACE
        bar = neg_2
        baz = mult_1
        const_1 = const(0.7)
        foo = const_1
        int_1 = int(neg_1, foo, 0.3)
        mult_1 = mult(bar, bar)
        neg_1 = neg(baz)
        neg_2 = neg(int_1)
        >>> print(s.name_computing_elements(strict=False).to_string())    # doctest: +NORMALIZE_WHITESPACE
        bar = neg(int_1)
        baz = mult(bar, bar)
        foo = const(0.7)
        int_1 = int(neg_1, foo, 0.3)
        neg_1 = neg(baz)

        Here one sees immediately that ``int_1`` is the actual integral solution while
        ``bar`` is only a derived quantity. Calls like ``const(float)`` remain unchanged
        since they are already in the normal form ``f(v1,v2,...)``.
        
        Here is a more complex example:
        
        >>> from dda.computing_elements import neg,int,mult
        >>> dda_state = State({"x": neg(int(neg(int(neg(mult(1, Symbol("x")), 0.005, 1)), 0.005, 0))) })
        >>> dda_state.name_computing_elements().variable_ordering().where_is # doctest: +NORMALIZE_WHITESPACE
        {'x': 'vars.aux.sorted',
        'mult_1': 'vars.aux.sorted',
        'neg_2': 'vars.aux.sorted',
        'neg_1': 'vars.aux.sorted',
        'int_1': 'vars.evolved',
        'int_2': 'vars.evolved'}

        """
        symbol_counter = collections.defaultdict(lambda:0)
        intermediates = {}
        #NamedSymbol = collections.namedtuple('NamedSymbol', ['symbol', 'number'])
        def register_computing_element(el):
            if len(el.tail) and not el in intermediates:
                symbol_counter[el.head] += 1
                named_symbol = "%s_%d" % (el.head, symbol_counter[el.head])
                while named_symbol in self:
                    # Note that this naming clash could also happen by pure coincidence.
                    warnings.warn(f"State.named_computing_elements(): While counting {el.head}, I notice that  {named_symbol} is already part of the state. Maybe you want to run name_computing_elements(strict=False) for idempotence.")
                    named_symbol += "_"
                intermediates[named_symbol] = el
                return Symbol(named_symbol)
            return el
        
        linearized_state = self.map_tails(register_computing_element, map_root=strict)
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
            intermediate variables called like ``int_0``, ``int_1``(see :meth:`name_computing_elements`
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
        
        Given an ODE problem ``dq/dt = f(q)``, an imperative code for evolving the state
        ``q`` in time  should compute all auxillairy variables in the respective order
        before computing the actual ``dq/dt``. The dependency is basically, in pseudo code:
        
        >>> aux  = function_of(aux, state)                    # doctest: +SKIP
        >>> dqdt = function_of(aux, state)                    # doctest: +SKIP
        
        and in the numerical integration schema step
        
        >>> state = function_of(dqdt)                         # doctest: +SKIP
        
        This method returns a namespace object, which is basically a fancy dictionary. It
        is used over a simple dictionary just for shorter syntax.
        
        The following examples demonstrate a deeply nested corner case, i.e. a 
        compute graph consisting of a single "long" Euler cycle. By breaking up this
        cycle at the integrations, ``variable_ordering()`` can linearize these cycles
        correctly. This works both for non-strict and strict element naming.
        
        >>> from dda.computing_elements import neg,int,mult
        >>> dda_state = State({"x": neg(int(neg(int(neg(mult(1, Symbol("x")), 0.005, 1)), 0.005, 0))) })
        >>> # variable ordering is made based on non-strict naming:
        >>> dda_state.name_computing_elements(strict=False) # doctest: +NORMALIZE_WHITESPACE
        State({'int_1': int(neg_1),
               'int_2': int(neg_2),
               'mult_1': mult(1, x),
               'neg_1': neg(mult_1, 0.005, 1),
               'neg_2': neg(int_1, 0.005, 0),
               'x': neg(int_2)})
        >>> dda_state.name_computing_elements(strict=True) # doctest: +NORMALIZE_WHITESPACE
        State({'int_1': int(neg_1),
        'int_2': int(neg_2),
        'mult_1': mult(1, x),
        'neg_1': neg(mult_1, 0.005, 1),
        'neg_2': neg(int_1, 0.005, 0),
        'neg_3': neg(int_2),
        'x': neg_3})
        >>> # This is how the full output looks like
        >>> dda_state.variable_ordering()  # doctest: +SKIP
        namespace(aux=namespace(all=['mult_1', 'neg_1', 'neg_2', 'x'],
                                sorted=['x', 'mult_1', 'neg_2', 'neg_1'],
                                cyclic=[],
                                unneeded=set()),
                  evolved=['int_1', 'int_2'],
                  explicit_constants=[],
                  all=['int_1', 'int_2', 'mult_1', 'neg_1', 'neg_2', 'x'],
                  ordering=OrderedDict([('vars.explicit_constants', []),
                                        ('vars.aux.sorted',
                                         ['x', 'mult_1', 'neg_2', 'neg_1']),
                                        ('vars.aux.cyclic', []),
                                        ('vars.evolved', ['int_1', 'int_2']),
                                        ('vars.aux.unneeded', set())]),
                  where_is={'int_1': 'vars.evolved',
                            'int_2': 'vars.evolved',
                            'mult_1': 'vars.aux.sorted',
                            'neg_1': 'vars.aux.sorted',
                            'neg_2': 'vars.aux.sorted',
                            'x': 'vars.aux.sorted'})
        >>> # Compare the strict and nonstrict orderings:
        >>> for k, v in dda_state.variable_ordering().ordering.items(): print(f"{k:25s}: {v}")
        vars.explicit_constants  : []
        vars.aux.sorted          : ['x', 'mult_1', 'neg_2', 'neg_1']
        vars.aux.cyclic          : []
        vars.evolved             : ['int_1', 'int_2']
        vars.aux.unneeded        : set()
        >>> for k, v in dda_state.name_computing_elements(strict=True).variable_ordering().ordering.items(): print(f"{k:25s}: {v}")
        vars.explicit_constants  : []
        vars.aux.sorted          : ['neg_3', 'x', 'mult_1', 'neg_2', 'neg_1']
        vars.aux.cyclic          : []
        vars.evolved             : ['int_1', 'int_2']
        vars.aux.unneeded        : set()
        
        """
        
        lin = self.name_computing_elements(strict=False)
        vars = types.SimpleNamespace() # VariableTaxonomy()
        vars.aux = types.SimpleNamespace() # VariableTaxonomy()
        
        # Thanks to named computing elements, can find all int(...) expressions
        # without searching, since they must come first.
        vars.evolved  = sorted(filter(lambda var: lin[var].head in ["int", "diff"],   lin))
        vars.explicit_constants = sorted(filter(lambda var: lin[var].head == "const", lin))
        
        # Then compute ALL aux variables BEFORE computing dqdt.
        # The order of dqdt should not be touched, as there CAN NOT be any
        # dependency, since dqdt.foo = int(lin).

        vars.all = sorted(set.union(*[set(map(str, lin[k].all_variables())) for k in lin], set(lin)))
        vars.aux.all = [ v for v in vars.all if not v in vars.evolved and not v in vars.explicit_constants  ]

        # Linearize aux expressions by dependency sorting.
        dep_edge_list = lin.dependency_graph()
        # Edge direction: (a,b) = [dependent variable a]--[depends on]-->[dependency b]
        aux_dep_edges = [ (a,b) for a,b in dep_edge_list if b in vars.aux.all ]  # a in vars.aux.all and
        # Note:
        #  In order to detect auxers dependent on evolved vars, we only filter for b being aux and let a free.
        #  We cannot feed the dep_edge_list directly into topological_sort since it would yield cyclic
        #  dependency for any meaningful compute circuit, which always has feedback loops.
        #  These loops are breaked by the evolved variables.
        dep_sorted, dep_cyclic = topological_sort(aux_dep_edges)
        vars.aux.sorted = [ v for v in dep_sorted if v in vars.aux.all ]
        vars.aux.cyclic = [ v for v in dep_cyclic if v in vars.aux.all ]

        vars.aux.unneeded = set(vars.aux.all) - (set(vars.aux.sorted) | set(vars.aux.cyclic) | set(vars.explicit_constants))
        
        # The following is an evil eval trick to avoid repetition. It just dumps the content of the mentioned vars.[...] arrays.
        ordering = ["vars.explicit_constants", "vars.aux.sorted", "vars.aux.cyclic", "vars.evolved", "vars.aux.unneeded"]
        vars.ordering = collections.OrderedDict([ (name, eval(name, {"vars":vars})) for name in ordering ])
        
        # allow inverse lookup for debugging
        vars.where_is = { i: k  for k,l in vars.ordering.items() for i in l }
        
        # In the end, make sure we haven't lost something!
        residium = set(lin.keys()) - set(vars.where_is.keys())
        if len(residium) != 0: 
                warnings.warn("State.variable_ordering(): Lost these variables in ordering analysis: " + str(residium))
                # could also raise an issue, because it is kind of serious.
        
        return vars

    def remove_duplicates(self):
        """
        Assuming a linearized state, this function simplifies the system by removing/resolving
        duplicate entries. No further renaming takes place: Always the first encounter of a
        term determines the name for all equivalent terms.
        
        Returns a new state.
        """
        # 1. equivalence classes (master_key: [equivalents]} and reverse lookup values {term: master_key}
        classes, values = {}, {}
        for i,iv in self.items():
            if iv in values:
                classes[ values[iv] ].append(i)
            else: # new equivalence class
                classes[ i ] = []
                values[ iv ] = i
        # 2. Create the new state based on the equivalence classes
        #    Start with a straight copy of the master classes
        ret = State({ master: self[master] for master in classes.keys() })
        # 3. Recurvsively replace equivalent class members in any term in ret
        for master, equivalents in classes.items():
            slave2master = lambda varname: master if varname in equivalents else varname
            for testkey, testval in ret.items():
                ret[testkey] = testval.map_variables(slave2master, returns_symbol=False)
        return ret
    
    def term_statistics(self):
        """
        Assuming a linearized state, tells how much each term occurs within this state.
        Returns instance of ``collections.Counter``. For simplicity, the term heads
        are returned as strings.
        
        Typical usage is like ``state.name_computing_elements().remove_duplicates().term_statistics()``
        """
        return collections.Counter([ term.head for term in self.values() ])
        

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


