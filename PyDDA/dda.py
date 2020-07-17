#!/usr/bin/env python3

"""
PyDDA is a small library to write and generate DDA code in Python.
DDA stands for digital differential analyzer. In this context, it is
a code for solving ordinary differential equations given in a domain
specific language description (i.e. an electrical circuit).

The main advantage of this implementation in contrast to the older Perl
implementation is abstract syntax tree level of circuit representation.
The syntax tree representation allows for fine-grained manipulations of
terms where the older Perl code could only apply regular expressions.

This code can replace the dda2c.pl Perl implementation. It is a
standalone Python 3 code with no third party dependencies. It generates
standalone C++ code with no dependencies (not even on dda.h).

This module can either be used from a DDA file written in Python or 
directly from old-style traditional DDA plaintext files. While pythonic
dda files have the advantage to be able to use all the flexibility of
Python scripting (such as using numpy for linear algebra computations
and matplotlib for postprocessing of results), plaintext DDA files are
in general shorter and more precise to read.

The dda.py file can also be used as a command line utility. The
behaviour is similar to the simulate.pl and dda2c.pl utilities but also
covers a few more features.

Known Bugs and limitations: (Amongst others)

(1) Aliasing

> state.foo = f(...)
> state.bar = state.foo

doesn't resolve (state must point to terms, not variables)

Written in June 2020 by SvenK.
Will be Open Sourced within the Analog R&D project.
"""

# There are no dependencies. All Python included.
import os, sys, textwrap, itertools, pprint, collections, types, builtins
flatten = lambda l: [item for sublist in l for item in sublist]
unique = lambda l: list(set(l))

assert sys.version_info >= (3, 6), \
   "We use f-strings, which require Python 3.6. Just remove them to continue."

# Ladies and gentlemen, what follows on the next 200 lines is the
# smallest pythonic AST implementation on the northern hemnisphere.
# Look ma, no dependencies!

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

# Here is a list of well-known DDA functions:
dda_functions = "const neg div int sum mult dead_upper dead_lower min max lt le gt ge sqrt abs exp floor".split()
dda_symbols = { k: Symbol(k) for k in dda_functions }

# This allows for easy namespace access:
dda = types.SimpleNamespace(**dda_symbols)

# In order to access the dda functions in your global namespace, run this code:
# > globals().update(dda_symbols)
# Globals are module-local, so we cannot provide this as a function

# The implementation is given directly in the target language
c_impl = """
/* if you use an old C++ compiler, just remove the newer features */
#define A constexpr double            /* constexpr requires C++11 */
#define D template<typename... T> A   /* Variadic templates require C++17 */

// Known limitations for div(int, double): If certain arguments appear as integer
// in the code (i.e. 1 instead of 1.0), there is div(int,int) kicking in from
// cstdlib. TODO: Should rename div to Div; following int->Int.

A neg(double a) { return -a; }
A div(double a, double b) { return a/b; }
D Int(T... a) { return -(a + ...); } // int() is reserved in C
D sum(T... a) { return -(a + ...); }
D mult(T... a) { return (a * ...); }
A dead_upper(double a, double b) { return a > b ? (a-b) : 0; }
A dead_lower(double a, double b) { return a < b ? (a-b) : 0; }
A min(double a, double b) { return a < b ? a : b; }
A max(double a, double b) { return a > b ? a : b; }
A lt(double a, double b, double c, double d) { return a <  b ? c : d; }
A le(double a, double b, double c, double d) { return a <= b ? c : d; }
A gt(double a, double b, double c, double d) { return a >  b ? c : d; }
A ge(double a, double b, double c, double d) { return a >= b ? c : d; }
// A sqrt(double a) is part of <cmath>
A abs(double a) { return a < 0 ? -a : a; } // abs(int) part of cstdlib
// A exp(double a) is part of <cmath>
A floor(double a) { return (int)(a); } // also part of cmath since c++11
"""

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


class exporter:
    def __init__(self, state, **kw):
        self.__dict__.update(kw) # bit ugly parameter passing
        self.state = state
        self.run() # should be chainable (return self) and set self.output [str]
        
    def arg(self, name, default=None): # sugar
        return self.__dict__.get(name, default)
    
    def print(self, to=sys.stdout):
        if isinstance(to, str): to = open(to, "w") # a neat service
        if not hasattr(self, "output"): self.run()
        print(self.output, file=to)
        self.output_filename = to.name
        return self # chainable

class cpp_code_generator(exporter):
    """
    Allows for compiling DDA to a standalone C++ code.
    """
    
    # TBD FIX indentation: https://stackoverflow.com/questions/2504411/proper-indentation-for-python-multiline-strings
    # using textwrap.dedent, i guess
    cpp_template = """\
    // This code was generated by PyDDA.

    #include <cmath> /* don't forget -lm for linking */
    #include <cfenv> /* for feenableexcept */
    #include <limits> /* for signaling NAN */
    #include <cstdio>

    constexpr double %(nan_name)s = std::numeric_limits<double>::signaling_NaN();

    %(c_impl)s

    // Time-evolved variables, actual "state" (in general dq/dt!=0)
    struct %(state_type)s {
        %(state_var_definition)s
        %(dqdt_operators)s
    };

    // Auxiliary variables, derived from %(state_type)s, not evolved in time (dqdt=0)
    struct %(aux_type)s  {
        %(aux_var_definition)s
        void set_to_nan() {
            %(aux_var_set_to_nan)s
        }
    };

    /// Compute the equations as given in the dda file
    /// It is actually %(dqdt_name)s = f(%(state_name)s, %(aux_name)s), or at least
    /// (%(dqdt_name)s,%(aux_name)s) = f(%(state_name)s).
    /// %(aux_name)s is only returned for debugging and controlling purposes of intermediate results
    void f(%(state_type)s const &%(state_name)s, %(state_type)s &%(dqdt_name)s, %(aux_type)s &%(aux_name)s) {
        %(aux_name)s.set_to_nan(); // only for debugging: ensure no use of uninitialized variables

    %(equations)s
    }

    %(state_type)s
        initial_data{ %(initial_data)s },
        dt{ %(timestep_data)s };

    %(state_type)s simulate_dda(%(state_type)s initial, int max_iterations, int modulo_write, int rk_order) {
        %(state_type)s k1, k2, k3, k4, z, %(state_name)s=initial;
        %(aux_type)s %(aux_name)s;

        for(int iter = 0; iter < max_iterations; iter++) {
            switch(rk_order) {
                case 1:
                    // Explicit Euler scheme
                    f(%(state_name)s, k1, %(aux_name)s);
                    %(state_name)s = %(state_name)s + k1*dt;
                    break;
                case 2:
                    // RK2 scheme
                    f(%(state_name)s, k1, %(aux_name)s);
                    f(%(state_name)s + k1*dt, k2, %(aux_name)s);
                    %(state_name)s = %(state_name)s + (k1+k2)*dt*0.5;
                    break;
                case 3:
                    // Kutta's third order scheme 
                    f(%(state_name)s, k1, %(aux_name)s);
                    f(%(state_name)s + dt*k1*0.5, k2, %(aux_name)s);
                    f(%(state_name)s + dt*k1*(-1.0) + dt*k2*2.0, k3, %(aux_name)s);
                    %(state_name)s = %(state_name)s + (k1 + k2*4.0 + k3*1.0)*dt*(1./6.);
                    break;
                case 4:
                    // Classical RK4 scheme 
                    f(%(state_name)s, k1, %(aux_name)s);
                    f(%(state_name)s + dt*k1*0.5, k2, %(aux_name)s);
                    f(%(state_name)s + dt*k2*0.5, k3, %(aux_name)s);
                    f(%(state_name)s + dt*k3*1.0, k4, %(aux_name)s);
                    %(state_name)s = %(state_name)s + (k1 + k2*2.0 + k3*2.0 + k4)*dt*(1./6.);
                    break;
                default:
                    exit(-42);
            }

            if(iter %% modulo_write == 0) {
                printf(%(writer_formatstring)s, %(writer_format_arguments)s);
            }
        }

        return %(state_name)s;
    }

    int main(int argc, char** argv) {
        feenableexcept(FE_DIVBYZERO | FE_INVALID | FE_OVERFLOW);

        puts(%(writer_header)s); // Write CSV header
        
        int modulo_write = %(modulo_write)d,
            max_iterations = %(max_iterations)d,
            rk_order = %(rk_order)d;
        
        simulate_dda(initial_data, max_iterations, modulo_write, rk_order);
    }
    
    """

    def run(self):
        indent = " "*5 # or tab, whatever you prefer - should be fit to cpp_template
        
        # Despite all user-chosen variable names are scoped within structs/classes, name
        # clashes are possible in some contexts. Therefore, the following names should be
        # chosen carefully.
        state_type, aux_type = "state_variables", "auxillaries"
        state_name, dqdt_name, aux_name, other_name = "_state", "_dqdt", "_aux", "_other"
        nan_name = "_nan_"
        
        state = self.state.name_computing_elements()

        # Thanks to named computing elements, can find all int(...) expressions
        # without searching, since they must come first.
        evolved_variables = sorted(filter(lambda var: state[var].head == "int", state))

        # prepare for prefixing all RHS variables
        struct_for = lambda name: state_name if name in evolved_variables else aux_name
        prefix_rhs = lambda el: Symbol(f"{struct_for(el.head)}.{el.head}") if el.is_variable() else el
        # Remove any const() which remained. Would be nicer to assert not having consts() at all.
        remove_const = lambda x: x.tail[0] if isinstance(x,Symbol) and x.head=="const" else x

        # rename reserved keywords in the C language
        #c_names = { "const": "constant", "int": "Int", "div": "Div" }
        #c_substitute = lambda head: c_names.get(head, head)
        #c_state = State({ var: map_heads(state[var], c_substitute) for var in state })
        
        # Extract int(..., timestep, initial_data) and rewrite reserved C keyword
        timesteps = {}
        initial_data = {}
        def map_and_treat_integrals(var):
            if not var in evolved_variables: return state[var]
            tail = state[var].tail
            if not len(tail) >= 3: raise ValueError("int(...) requires at least int(value, dt, ic)")
            timesteps[var] = remove_const(tail[-2])
            initial_data[var] = remove_const(tail[-1])
            return Symbol("Int", *tail[0:len(tail)-2])
        state = State({ var: map_and_treat_integrals(var) for var in state })
        
        # Sort ONLY aux variables. Check that they DO NOT have any
        # cyclic dependency, because this would crash any circuitery anyway.
        #
        # Then compute ALL aux variables BEFORE computing dqdt.
        # The order of dqdt should not be touched, as there CAN NOT be any
        # dependency, since dqdt.foo = int(state).
        #
        # The dependency is basically
        #   aux = function_of(aux, state)
        #   dqdt = function_of(aux, state)
        # and in the integration schema step
        #   state = function_of(dqdt)
        
        all_vars = sorted(set.union(*[set(map(str, state[k].all_variables())) for k in state], state))
        aux_variables = [ v for v in all_vars if not v in evolved_variables  ]
        
        # Linearize aux expressions by dependency sorting.
        dep_edge_list = state.dependency_graph()
        # Edge direction: (a,b) = [dependent variable a]--[depends on]-->[dependency b]
        aux_dep_edges = [ (a,b) for a,b in dep_edge_list if a in aux_variables and b in aux_variables ]
        #sorted_vars, cyclic_vars = topological_sort(dep_edge_list)
        sorted_aux_vars, cyclic_aux_vars = topological_sort(aux_dep_edges)
        #all_vars = sorted_vars + cyclic_vars
        # aux_variables = set(all_vars) - set(evolved_variables) but preserving sorting.
        
        self.unneeded_auxers = set(aux_variables) - (set(sorted_aux_vars) | set(cyclic_aux_vars))

        # do the renaming *after* variable dependency analysis
        state = state.map_tails(remove_const)
        state = state.map_tails(prefix_rhs)
            
        # C-format lists of statements or so. Do indentation.
        J = lambda whatever: ", ".join(whatever)
        C = lambda whatever: textwrap.indent(whatever if isinstance(whatever, str) else  "\n".join(whatever), indent)
        CC = lambda whatevr: C(C(whatevr)) # two indentations ;-)
        varlist = lambda ctype, lst: C(textwrap.wrap(f"{ctype} {', '.join(lst)};", width=50))
    
        state_var_definition = varlist("double", evolved_variables)
        aux_var_definition = varlist("double", aux_variables)
        all_variables_as_string = C('"'+v+'",' for v in all_vars)
        
        # For debugging:
        aux_var_set_to_nan = C(f"{v} = {nan_name};" for v in aux_variables)
        
        initial_data = J(f"{initial_data[v]}" for v in evolved_variables)
        timestep_data = J(f"{timesteps[v]}" for v in evolved_variables)
        
        #state_assignments = lambda lst: C(f"{v} = {state[v]};" for v in lst)) if lst else C("/* none */")
        state_assignments = lambda lhs_struct,lst: [f"{lhs_struct}.{v} = {state[v]};" for v in lst] if lst else ["/* none */"]
        
        equations = []
        equations.append("// 1. Topologically sorted aux variables")
        equations += state_assignments(aux_name, sorted_aux_vars)
        equations.append("// 2. Cyclic aux variables")
        equations += state_assignments(aux_name, cyclic_aux_vars)
        equations.append("// 3. State variable changes (dqdt), finally")
        equations += state_assignments(dqdt_name, evolved_variables)
        equations.append("// 4. Unneeded auxilliary variables (maybe postprocessing, etc.)")
        equations += state_assignments(aux_name, self.unneeded_auxers)
        equations = C(equations)
        
        writer_fields = self.arg("writer_fields", default=all_vars)
        writer_header = '"'+" ".join(writer_fields)+'"'
        writer_format_arguments = J(f"{struct_for(v)}.{v}" for v in writer_fields)
        writer_formatstring = '"'+" ".join('%f' for v in writer_fields)+"\\n\""
        
        make_operator = lambda operator_symbol, other_type, a=True: [ \
            f"{state_type} operator{operator_symbol}(const {other_type} &{other_name}) const "+'{', \
            C(f"{state_type} {state_name};"), \
            C(f"{state_name}.{v} = {v} {operator_symbol} {other_name}{'.'+v if a else ''};" for v in evolved_variables), \
            C(f"return {state_name};"), \
            "}"]

        dqdt_operators = C(C(make_operator(s,o,a)) for s,(o,a) in
            itertools.product("*+", zip((state_type, "double"), (True,False))))
        
        # TODO: make user-definable
        modulo_write = self.arg("modulo_write", default=20)
        max_iterations = self.arg("max_iterations", default=30000)
        rk_order = self.arg("rk_order", default=1)
        
        self.output = self.cpp_template % {**locals(), **globals()}
        
#    def compile(self, compiler="g++", compiler_output="a.out", options="-Wall"):
#       "Can use: self.compile().run()"
#        if not hasattr(self, "output_filename"): self.print() # todo: Check for stdout, cannot compile then.
#        if system(f"{compiler} -o{compiler_output} {options} {self.output_filename}"): raise ValueError("Could not compile C source!")
#        class compiled_binary:
#            def run(self, scratch_file="test.csv")
#                if system(f"./{compiler_output} > {scratch_file}"): raise ValueError("Could not execute simulation!");
#        return compiled_binary()

    
class traditional_dda_exporter(exporter):
    """
    Export state to canonical dda file format (i.e. without all the python).
    """
    
    def run(self):
        # Not sure about scattered consts, maybe just remove them for the time being.
        remove_const = lambda x: x.tail[0] if isinstance(x,Symbol) and x.head=="const" else x
        state = self.state.map_tails(remove_const)
        # TODO: Treat constants better. They have deserved it!
        
        dda_lines = []
        dda_lines.append("# Canonical DDA file generated by PyDDA")
        dda_lines.append("")
        for k in sorted(state):
            dda_lines.append(f"{k} = {state[k]}")
        dda_lines.append("")
        
        self.output = "\n".join(dda_lines)

class to_sympy(exporter):
    def run(self):
        """
        Export a state to a set of equations for SymPy.
        Returns a list of sympy.Eq objects.
        Of course it requires Sympy installed/available.
        
        With Sympy, you can do all funny things, such as:
        > ss = export(state).to_sympy()
        > import sympy
        > print(sympy.latex(ss)) # Will pretty-print simplified equations
        """
        import sympy
        
        state = self.state
        
        symbol_mapper = self.arg("symbol_mapper", lambda x:x)
        sympy_Symbol = lambda label: sympy.Symbol(symbol_mapper(label))
        
        # round large floats. Doesn't work yet.
        rhs_rounder = lambda rhs: sympy.N(rhs, n=self.arg("round_n", 15))
        
        int = builtins.int # just to go sure
        t = sympy_Symbol("t")
        
        def todo(*x):
            raise ValueError("Requried DDA 2 Sympy function yet implemented")
        
        dda2sympy = {
            "const": lambda x: x,
            "neg":   lambda x: -x,
            "div":   lambda x,y: x/y,
            "int":   lambda *x: - sympy.Integral(sympy.Add(*x), t),
            "sum":   lambda *x: - sympy.Add(*x),
            "mult":  sympy.Mul,
            "sqrt":  sympy.sqrt,
            "abs":   sympy.Abs,
            "exp":   sympy.exp,
            "floor": sympy.floor,
        }
        
        def symbol2sympy(smbl):
            if isinstance(smbl, float) or isinstance(smbl, int):
                return smbl # let Sympy handle the numbers
            if not isinstance(smbl, Symbol): raise TypeError(f"Expecting symbol, got {smbl}")
            if smbl.is_variable():
                return sympy_Symbol(smbl.head) # just a variable
            else: # symbl.is_term()
                if smbl.head in dda2sympy:
                    return dda2sympy[smbl.head](*map(symbol2sympy, smbl.tail))
                else:
                    raise ValueError(f"DDA Symbol {smbl.head} in expression {smbl} not (yet) implemented.")
        
        self.equation_list = [ sympy.Eq(sympy_Symbol(lhs), rhs_rounder(symbol2sympy(state[lhs])))  for lhs in sorted(state) ]
    
        # Pretty-print set of equations. That's nicer then just
        # sympy.latex(self.equation_list)
        s = [ f"{sympy.latex(eq.lhs)} &= {sympy.latex(eq.rhs)}" for eq in self.equation_list ]
        equation_list_to_align = lambda t: r"\begin{align}"+"\n" + (r" \\"+"\n").join(t) + "\n\end{align}"
        
        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
        
        chunk_n = self.arg("chunk_equations", None)
        self.latex = "\n".join(map(equation_list_to_align, chunks(s,chunk_n) if chunk_n else [s]))
        self.output = self.latex # just a pretty-print version
    

def export(state, to, **kw):
    exporters = { "c": cpp_code_generator, "dda": traditional_dda_exporter, "sympy": to_sympy }
    if not to.lower() in exporters:
        raise ValueError(f"Export format {to} not known. Valid are {exporters.keys()}.")
    return exporters[to.lower()](state, **kw)


def read_traditional_dda(content, return_ordered_dict=False):
    """
    Read some traditional dda file. We use the Python parser (ast builtin package)
    for this job. This is possible because the DDA syntax is a python subset and
    the parser doesn't care about semantics, only syntax.
    Thanks to the ast builtin package, we can just transform the python AST to
    the Symbolic/State class data structures used in this module.
    
    If some of the assertions fail, you can debug your DDA file by inspecting
    the output of ast.parse(content) on iPython. You can also run the Python
    debugger (pdb) on this function, for instance in iPython:
    
    > %pdb
    > read_traditional_dda(file("foo.dda").read())
    
    Returns a state instance or OrderedDict, on preference.
    """
    import ast # python builtin
    tree = ast.parse(content)
    
    assert type(tree) == ast.Module, "I was expecting a whole file as content"
    assert type(tree.body) == list, "DDA file malformed, I was expecting a list of statements"
    assert all(type(f) == ast.Assign for f in tree.body), "DDA file malformed, I was expecting a list of assignments only"
    
    def arg2symbol(argument):
        "Transform some DDA function argument to the Symbol hierarchy"
        expr_as_str = ast.get_source_segment(content, argument) 
        if isinstance(argument, ast.Constant):
            return argument.value
        elif isinstance(argument, ast.Name):
            return argument.id
        elif isinstance(argument, ast.Call):
            return call2symbol(argument)
        else:
            raise TypeError(f"Don't understand argument '{expr_as_str}'")
    
    def call2symbol(statement):
        "Transform some Right Hand Side nested function call to Symbol hierarchy"
        expr_as_str = ast.get_source_segment(content, statement) # for debugging, can also print ast.dump(statement)
        assert type(statement) == ast.Call, f"Was expecting a simple f(x) call but got '{expr_as_str}'"
        assert len(statement.keywords) == 0, f"Did not expect pythonic keyword arguments f(x=bar) in '{expr_as_str}'"
        assert type(statement.func) == ast.Name, f"Dunno, what is {statement.func}?"
        head = statement.func.id
        tail = map(arg2symbol, statement.args)
        return Symbol(head, *tail)
    
    def ast_assignment_to_tuple(assign):
        line = ast.get_source_segment(content, assign) # for debugging, can also print ast.dump(assign)
        assert len(assign.targets)==1, f"Was expecting only a single assignment, but got '{line}'"
        assert type(assign.value) == ast.Call, f"DDA file malformed, expecting foo=call(bar), but got '{line}'."
        variable_name = assign.targets[0].id
        rhs = call2symbol(assign.value)
        return (variable_name, rhs)
    
    result = map(ast_assignment_to_tuple, tree.body)
    mapping = collections.OrderedDict(result)
    return mapping if return_dict else State(mapping)


# Here come dragons: The following lines define a couple of handy variables
# which can be used to write brever scripts. However, one probably does not
# want to import them.
#
# Here is the big CAVEAT: The following will OVERWRITE python internals such
# as int, sum, min, max. This can lead to very strange errors.
# Note that you can always access the Python builtins by importing builtins
# and using builtins.int, builtins.sum, etc.
#

# First, let's be nice and provide an instance:
state = State()

# Second, populate module namespace with well known DDA-registered functions:
globals().update(dda_symbols)

# The above line is equivalent to:
#const, neg, div, int, sum, mult, dead_upper, dead_lower, min, max, lt, le, gt, ge, sqrt, abs, exp, floor = symbols("\
#const, neg, div, int, sum, mult, dead_upper, dead_lower, min, max, lt, le, gt, ge, sqrt, abs, exp, floor")

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
