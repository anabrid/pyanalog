"""
C++ code generation is a major feature of the PyDDA code. The generated
code is built from a string template and has the following features:

* Standalone code: No further dependencies (beyond standard libc, lm and STL).
* Lightweight object oriented: Uses classes (structures) to hold the
  different variables (basically AoS instead of SoA approach). Little
  C++ templating.
* Organization in a few functions which allows to edit the generated 
  C++ code manually afterwards without going mad.
* CSV or binary output, or no output at all. Output is always made
  to stdout. Information messages are always sent to stderr.
* Debugging facilities built right into the code for setting NaNs and
  abortion in case of floating point exceptions.
* Runtime arguments via the commandline (argv): Parsing and passing.

.. note::

   **C++17** is required for building the C++ code. This is because
   we use variadic templates.

For the runtime arguments, we support so far:

- *Simulation steering*: Selection of number of integration iterations
  and frequency of dumping the solution.
- *Query based plotting*: Selection which variables shall be outputted
  at runtime.
- Further *Flags* and *Numeric arguments* as well as a useful ``--help``
  message.

We still hardcode at code generation time:

- Initial data
- time step sizes
- Variables and equation structure

"""

from .ast import State, Symbol, topological_sort
from .computing_elements import cpp_impl

# could also say is_number = lambda obj: str(obj).is_digit()
is_number = lambda obj: isinstance(obj, float) or isinstance(obj, int)

import textwrap, itertools, math

cpp_template = """\
// This code was generated by PyDDA.

#include <cmath> /* don't forget -lm for linking */
#include <cfenv> /* for feraisexcept and friends */
#include <limits> /* for signaling NAN */
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <map>
#include <cstdio>
#include <iostream>
#include <fstream>

bool debug;
constexpr double %(nan_name)s = std::numeric_limits<double>::signaling_NaN();

namespace dda {
%(cpp_impl)s
} // end namespace dda

using namespace dda;

// Time-evolved variables, actual "state" (in general dq/dt!=0)
struct %(state_type)s {
    %(state_var_definition)s
    %(dqdt_operators)s
    const double* byName(std::string %(lookup_name)s) const {
        %(state_vars_by_name)s
        return nullptr;
    }
};

// Auxiliary variables, derived from %(state_type)s, not evolved in time (dqdt=0)
struct %(aux_type)s  {
    %(aux_var_definition)s
    void set_to_nan() {
        %(aux_var_set_to_nan)s
    }
    const double* byName(std::string %(lookup_name)s) const {
        %(aux_vars_by_name)s
        return nullptr;
    }
};

// Explicit constants
static const struct %(const_type)s {
    %(explicit_constant_definitions)s
    const double* byName(std::string %(lookup_name)s) const {
        %(explicit_constants_by_name)s
        return nullptr;
    }
} %(const_name)s;

// All variables as well-ordered string:
static const std::vector<std::string> all_variables = {
    %(all_variables_as_string)s
};

/// Compute the equations as given in the dda file
/// It is actually %(dqdt_name)s = f(%(state_name)s, %(aux_name)s), or at least
/// (%(dqdt_name)s,%(aux_name)s) = f(%(state_name)s).
/// %(aux_name)s is only returned for debugging and controlling purposes of intermediate results

void f(%(state_type)s const &%(state_name)s, %(state_type)s &%(dqdt_name)s, %(aux_type)s &%(aux_name)s) {
    if(debug) %(aux_name)s.set_to_nan(); // only for debugging: ensure no use of uninitialized variables

    %(equations)s
}

/// Helper routine: Compute aux variables from a state. Helpful for consistent printing.
void compute_aux(%(state_type)s const& %(state_name)s, %(aux_type)s &%(aux_name)s) {
    %(state_type)s dummy_%(dqdt_name)s;
    f(%(state_name)s, dummy_%(dqdt_name)s, %(aux_name)s);
}

%(state_type)s
    initial_data{ %(initial_data)s },
    dt{ %(timestep_data)s };

void integrate(%(state_type)s& %(state_name)s, %(aux_type)s& %(aux_name)s, int rk_order) {
    %(state_type)s k1, k2, k3, k4;

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
}

struct csv_writer {
    std::vector<std::string> query_variables;
    bool write_initial_conditions, always_compute_aux_before_printing, binary_output;

    const char* sep(size_t i) const { return (i!=query_variables.size() ? "\\t" : "\\n"); }
    
    void write_header() const {
        if(binary_output) return;
        for(size_t i=0; i<query_variables.size();)
            std::cout << query_variables[i++] << sep(i);
    }
    
    void write_line(const %(state_type)s& %(state_name)s, const %(aux_type)s& %(aux_name)s, const %(const_type)s& %(const_name)s) const {
        %(aux_type)s recomputed__%(aux_name)s;
        const %(aux_type)s *actual__%(aux_name)s = &%(aux_name)s;
        if(always_compute_aux_before_printing) {
            compute_aux(%(state_name)s, recomputed__%(aux_name)s);
            actual__%(aux_name)s = &recomputed__%(aux_name)s;
        }
        for(size_t i=0; i<query_variables.size(); i++) {
            const double* lookup=nullptr; std::string var = query_variables[i];
            if(!lookup) lookup = %(state_name)s.byName(var);
            if(!lookup) lookup = actual__%(aux_name)s->byName(var);
            if(!lookup) lookup = %(const_name)s.byName(var);
            if(!lookup) { std::cerr << "Lookup failed" << std::endl; exit(-123); }
            if(binary_output) {
                std::cout.write(reinterpret_cast<const char*>( lookup ), sizeof(double));
            } else {
                std::cout << *lookup << sep(i+1);
            }
        }
    }
} writer;

%(state_type)s simulate_dda(%(state_type)s initial, int max_iterations, int modulo_writer, int rk_order) {
    %(state_type)s %(state_name)s = initial;
    %(aux_type)s %(aux_name)s;
    
    if(debug) {
#ifdef _GNU_SOURCE
        feenableexcept(FE_DIVBYZERO | FE_INVALID | FE_OVERFLOW); // glibc-specific
#else
        // Debugging for non-glibc (ie. non-Linux), see https://stackoverflow.com/a/12762999
        // If you want do debugging on some other platform, please implement it on your own...
        std::cerr << "Warning: Debugging floating point not yet supported" << std::endl;
#endif
    }

    writer.write_header();

    if(writer.write_initial_conditions) {
        %(aux_name)s.set_to_nan(); // definite state for auxers at printing: not yet computed.
        writer.write_line(%(state_name)s, %(aux_name)s, %(const_name)s);
    }
    
    for(int iter = 0; iter < max_iterations; iter++) {
        integrate(%(state_name)s, %(aux_name)s, rk_order);

        if(iter %% modulo_writer == 0)
            writer.write_line(%(state_name)s, %(aux_name)s, %(const_name)s);
    }
    
    return %(state_name)s;
}

using namespace std;

vector<string> split(const string& input, const char seperator='=') {
    stringstream s(input);
    string segment;
    vector<string> seglist;
    while(getline(s, segment, seperator))
        seglist.push_back(segment);
    return seglist;
}

template<typename T>  T extract(const string& input) {
    T target;
    istringstream ss(input); ss >> target;
    if(ss.fail()) {
        cerr << "Failure: Not a number: " << input << endl;
        exit(-4);
    }
    return target;
}

bool unprefix(string& str, const string prefix) {
    bool is_prefixed = !str.compare(0, prefix.size(), prefix);
    if(is_prefixed) str = str.substr(prefix.size());
    return is_prefixed;
}

bool contains(const std::vector<std::string>& haystack, const std::string& needle) {
    return std::find(haystack.begin(), haystack.end(), needle) != haystack.end();
}

int main(int argc, char** argv) {
    // runtime-definable arguments and their values:
    
    map<string, int> numbers;
    numbers["modulo_write"] = 1;
    numbers["max_iterations"] = 100;
    numbers["rk_order"] = 1;
    numbers["number_precision"] = 5;
    
    map<string, bool> flags;
    flags["debug"] = false;
    flags["list_all_variables"] = false;
    flags["write_initial_conditions"] = false;
    flags["always_compute_aux_before_printing"] = true;
    flags["binary_output"] = false;

    // Our primitive argument processing:
    vector<string> args(argv + 1, argv + argc);
    for(auto arg : args) {
        if(arg == "--help") {
            string ind = "  ";
            cerr << "Usage: " << argv[0] << " [arguments] <variables_to_print>" << endl;
            cerr << "This is an ODE integrator generated by PyDDA" << endl << endl;
            cerr << "* Boolean arguments (Usage --foo or --foo=1 or --foo=0)" << endl;
            for(auto const& [key, val] : flags) cerr << ind << key << " (default value: " << val << ")" << endl;
            cerr << "* Numeric arguments: (Usage --foo=123)" << endl;
            for(auto const& [key, val] : numbers) cerr << ind << key << " (default value: " << val << ")" << endl;
            cerr << "* Query fields: (if none given, all are dumped)";
            for(size_t i=0; i<all_variables.size();) { cerr << endl << ind;
                for(size_t j=0;j<5 && i<all_variables.size();j++) cerr << all_variables[i++] << (i!=all_variables.size() ? ", " : ""); }
            cerr << endl << "Exemplaric usage:" << endl;
            cerr << ind << argv[0] << "--foo=True --bar=7 var1 var2 var3" << endl;
            exit(-1);
        }
    
        if(unprefix(arg, "--")) {
            vector<string> splitted = split(arg);
            string key, value;
            if(splitted.size() == 1) splitted.push_back("1"); // for the booleans
            if(splitted.size() != 2) {
                cerr << "ERR: Illegal key-value argument " << arg << endl;
                cerr << "ERR: Try --help" << endl;
                exit(-3);
            }
            key=splitted[0]; value=splitted[1];
            if(numbers.count(key))    numbers[key] = extract<int>(value);
            else if(flags.count(key)) flags[key] = extract<bool>(value);
            else {
                cerr << "ERR: Illegal argument: " << arg << endl;
                cerr << "ERR: Try --help" << endl;
                exit(-3);
            }
        } else {
            if(contains(all_variables, arg)) {
                writer.query_variables.push_back(arg);
            } else {
                cerr << "ERR: Illegal argument: " << arg << endl;
                cerr << "ERR: It is not a member of the variables. Try --help." << endl;
                exit(-2);
            }
        }
    } // for args
    
    if(flags["list_all_variables"]) {
        for(auto var : all_variables) puts(var.c_str());
        exit(0);
    }
    
    // cout.set_precision(numbers["number_precision"]); // TODO, move above correctly, before every number
    
    if(writer.query_variables.empty())
        writer.query_variables = all_variables;

    debug = flags["debug"];
    writer.write_initial_conditions = flags["write_initial_conditions"];
    writer.always_compute_aux_before_printing = flags["always_compute_aux_before_printing"];
    writer.binary_output = flags["binary_output"];
    
    simulate_dda(initial_data, numbers["max_iterations"], numbers["modulo_write"], numbers["rk_order"]);
}

"""

def to_cpp(state, number_precision=math.inf):
    """
    Given a state, returns standalone C++ code as string.
    
    This code can be written to a file, compiled with a recent 
    C++ compiler and then solves the differential equation system when executed.
    
    The algorithm is basically:
    
    1. linearize the state (this can raise)
    2. determine all the C++ template fields
    3. Return the filled out template
    
    We plan to add logging for non-fatal information about the C++ code quality
    (see TODOs in the code).
    
    The argument ``number_precision`` currently has no effect.
    """

    indent = " "*5 # or tab, whatever you prefer - should be fit to cpp_template

    # Despite all user-chosen variable names are scoped within structs/classes, name
    # clashes are possible in some contexts. Therefore, the following names should be
    # chosen carefully.
    state_type, aux_type, const_type = "state_variables", "auxillaries", "constants"
    state_name, dqdt_name, aux_name, other_name, const_name = "_state", "_dqdt", "_aux", "_other", "_constants"
    lookup_name, nan_name = "_name_", "_nan_"

    state = state.name_computing_elements()
    vars = state.variable_ordering()
    
    # NB: One could require that there no implicit constants, i.e. numbers appearing randomly
    #     on the RHS of expressions. One could even go further and allow numbers only in
    #     potentiometer settings
    
    if not vars.evolved:
        pass # TODO: Warn that there are (interesting) variables at all.
    if vars.aux.cyclic:
        pass # TODO: Warn that there are unwanted feedback loops

    # prepare for prefixing all RHS variables
    pystruct2cprefix = { state_name: vars.evolved, aux_name: vars.aux.all, const_name: vars.explicit_constants  }
    struct_lookup = { var: cstruct for (cstruct, pystruct) in pystruct2cprefix.items()  for var in pystruct  }
    csymbol = lambda var: f"{struct_lookup[var]}.{var}"
    prefix_rhs = lambda el: Symbol(csymbol(el.head)) if el.is_variable() else el
    
    def number2cstr(number):
        if not is_number(number):
            raise ValueError(f"Was expecting a number, but got {type(number)} with value {number}.")
        formatstring = f"%{number_precision}f" if number_precision < math.inf else "%f"
        return formatstring % number
    
    # Remove any const() which remained. Would be nicer to assert not having consts() at all.
    remove_const = lambda x: number2cstr(x.tail[0]) if isinstance(x,Symbol) and x.head=="const" else x
    
    # Translate const(foo) by stripping foo or some bar by looking up if it is an explicit constant.
    # Dynamical variables are not allowed here.
    def lookup_const(var):
        if isinstance(var,Symbol):
            if var.head == "const":
                var = var.tail[0] # continue
            elif var.is_variable():
                if not var.head in vars.explicit_constants:
                    raise ValueError(f"Only constants allowed in this context. {var} however refers to {csymbol(var.head)}.")
                return csymbol(var.head)
            else: # remaining case: var.is_term()
                raise ValueError(f"Was expecting const(foo) or so, but got term {var}.")
        if not is_number(var): raise ValueError(f"Got a weird {type(var)} in a constant context: {var}")
        return number2cstr(var)

    # rename reserved keywords in the C language
    #c_names = { "const": "constant", "int": "Int", "div": "Div" }
    #c_substitute = lambda head: c_names.get(head, head)
    #c_state = State({ var: map_heads(state[var], c_substitute) for var in state })

    # Extract int(..., timestep, initial_data) and rewrite reserved C keyword
    timesteps = {}
    initial_data = {}
    def map_and_treat_integrals(var):
        if not var in vars.evolved: return state[var]
        tail = state[var].tail
        if not len(tail) >= 3: raise ValueError("int(...) requires at least int(value, dt, ic)")
        timesteps[var] = lookup_const(tail[-2])
        initial_data[var] = lookup_const(tail[-1])
        return Symbol("Int", *tail[0:len(tail)-2])
    state = State({ var: map_and_treat_integrals(var) for var in state })

    
    # do the renaming *after* variable dependency analysis
    state = state.map_tails(remove_const)
    state = state.map_tails(prefix_rhs)
        
    # C-format lists of statements or so. Do indentation.
    J = lambda whatever: ", ".join(whatever)
    C = lambda whatever: textwrap.indent(whatever if isinstance(whatever, str) else  "\n".join(whatever), indent)
    CC = lambda whatevr: C(C(whatevr)) # two indentations ;-)
    varlist = lambda ctype, lst: C(textwrap.wrap(f"{ctype} {', '.join(lst)};", width=50)) if lst else ""

    state_var_definition = varlist("double", vars.evolved)
    aux_var_definition = varlist("double", vars.aux.all)
    all_variables_as_string = C(f'"{var}",' for var in vars.all)
    
    # For runtime introspection capabilities
    lookup = lambda struct: CC(f'if({lookup_name} == "{var}") return &{var};' for var in struct)
    state_vars_by_name = lookup(vars.evolved)
    aux_vars_by_name = lookup(vars.aux.all)
    explicit_constants_by_name = lookup(vars.explicit_constants)

    # For debugging:
    aux_var_set_to_nan = C(f"{var} = {nan_name};" for var in vars.aux.all)
    
    # Workaround for avoiding logic in template...
    either = lambda lst, otherwise: lst if lst else [otherwise]
    nonemptyvarlist = lambda lst: either(lst, otherwise="_none=-1")
    
    explicit_constant_definitions = varlist("constexpr static double", 
        nonemptyvarlist([f"{var}={state[var].tail[0]}" for var in vars.explicit_constants])) # extract x in const(x)

    initial_data = J(str(initial_data[var]) for var in vars.evolved)
    timestep_data = J(str(timesteps[var]) for var in vars.evolved)

    #state_assignments = lambda lst: C(f"{v} = {state[v]};" for v in lst)) if lst else C("/* none */")
    state_assignments = lambda lhs_struct,lst: [f"{lhs_struct}.{var} = {state[var]};" for var in lst] if lst else ["/* none */"]

    # The dependency is basically
    #   aux = function_of(aux, state)
    #   dqdt = function_of(aux, state)
    # and in the integration schema step
    #   state = function_of(dqdt)
    
    equations = []
    equations.append("// 1. Topologically sorted aux variables")
    equations += state_assignments(aux_name, vars.aux.sorted)
    equations.append("// 2. Cyclic aux variables")
    equations += state_assignments(aux_name, vars.aux.cyclic)
    # FIXME:
    # There is a special case like the following where unneeded auxers are wrongly
    # detected as unneeded, depsite urgently needed:
    """
    # CONTEXT: dipole_water.py
     // 3. State variable changes (dqdt), finally
     _dqdt.mdm0_0 = Int(_aux.Fm0_01, _aux.Fn0_00, _aux.Fn0_01);
     _dqdt.mdm0_1 = Int(_aux.Fm0_01, _aux.Fn0_10, _aux.Fn0_11);
     _dqdt.mdm1_0 = Int(_aux.Fm1_01, _aux.Fn1_00, _aux.Fn1_01);
     _dqdt.mdm1_1 = Int(_aux.Fm1_01, _aux.Fn1_10, _aux.Fn1_11);
     _dqdt.mdr0_0 = Int(_aux.Fr0_01, _aux.Fn0_00, _aux.Fn0_01);
     _dqdt.mdr0_1 = Int(_aux.Fr0_01, _aux.Fn0_10, _aux.Fn0_11);
     _dqdt.mdr1_0 = Int(_aux.Fr1_01, _aux.Fn1_00, _aux.Fn1_01);
     _dqdt.mdr1_1 = Int(_aux.Fr1_01, _aux.Fn1_10, _aux.Fn1_11);
     _dqdt.mu0_0 = Int(_aux.mult_19);
     _dqdt.mu0_1 = Int(_aux.mult_37);
     _dqdt.mu1_0 = Int(_aux.mult_45);
     _dqdt.mu1_1 = Int(_aux.mult_51);
     _dqdt.r0_0 = Int(_aux.mult_20);
     _dqdt.r0_1 = Int(_aux.mult_38);
     _dqdt.r1_0 = Int(_aux.mult_46);
     _dqdt.r1_1 = Int(_aux.mult_52);
     // 4. Unneeded auxilliary variables (maybe postprocessing, etc.)
     _aux.mult_19 = mult(0.5, _state.mdm0_0);
     _aux.mult_46 = mult(0.0625, _state.mdr1_0);
     _aux.mult_52 = mult(0.0625, _state.mdr1_1);
     _aux.mult_51 = mult(0.5, _state.mdm1_1);
     _aux.mult_37 = mult(0.5, _state.mdm0_1);
     _aux.mult_45 = mult(0.5, _state.mdm1_0);
     _aux.mult_20 = mult(0.0625, _state.mdr0_0);
     _aux.mult_38 = mult(0.0625, _state.mdr0_1);
     """
    equations.append("// 3. Unneeded auxilliary variables (maybe postprocessing, etc.)")
    equations += state_assignments(aux_name, vars.aux.unneeded)
    equations.append("// 4. State variable changes (dqdt), finally")
    equations += state_assignments(dqdt_name, vars.evolved)
    equations = C(equations)

    make_operator = lambda operator_symbol, other_type, a=True: [ \
        f"{state_type} operator{operator_symbol}(const {other_type} &{other_name}) const "+'{', \
        C(f"{state_type} {state_name};"), \
        C(f"{state_name}.{var} = {var} {operator_symbol} {other_name}{'.'+var if a else ''};" for var in vars.evolved), \
        C(f"return {state_name};"), \
        "}"]

    dqdt_operators = C(C(make_operator(s,o,a)) for s,(o,a) in
        itertools.product("*+", zip((state_type, "double"), (True,False))))

    output = cpp_template % {**locals(), **globals()}
    return output

# What follows are a few helper functions to make the usage nicer

def compile(code, c_filename="generated.cc", compiler="g++", compiler_output="a.out", options="--std=c++17 -Wall"):
    """
    Small helper function to compile C++ code from python.
    
    Write string *code* to *c_filename* and run the *compiler* on that, afterwards.
    Will raise an error if compilation fails.
    """
    from os import system
    with open(c_filename, "w") as fh:
        print(code, file=fh)
    if system(f"{compiler} -o{compiler_output} {options} {c_filename}"):
        raise ValueError("Could not compile C source!")

def run(command="./a.out", return_ndarray=True, arguments={}, fields_to_export=[]):
    """
    Small helper function to execute a code generated by this module.
    
    Runs *command* on the command line, with named *arguments* in ``--foo=bar``
    fashion and *fields_to_export* just as a sequential argument list.
    
    Pipes stdout to a string, which is returned. Stderr will just be passed.
    The function will return once the binary finished or raise in case of error.
    
    Example usage:
    
    >>> from dda import *
    >>> state = State()
    >>> state["x"] = Symbol("int", Symbol("neg", state["x"]), 0.2, 1)
    >>> state
    State({'x': int(neg(x), 0.2, 1)})
    >>> cpp_code = to_cpp(state)
    >>> print('Generated code has about %d lines' % cpp_code.count('\\n')) # doctest: +SKIP
    Generated code has about 333 lines
    >>> compile(cpp_code, compiler_output="foo.exe")
    >>> res = run("./foo.exe", arguments={'max_iterations':20}, fields_to_export=['x'])
    Running: ./foo.exe --max_iterations=20 x
    >>> res["x"]
    array([ 1.2    ,  1.44   ,  1.728  ,  2.0736 ,  2.48832,  2.98598,
            3.58318,  4.29982,  5.15978,  6.19174,  7.43008,  8.9161 ,
           10.6993 , 12.8392 , 15.407  , 18.4884 , 22.1861 , 26.6233 ,
           31.948  , 38.3376 ])

    """
    import subprocess, io, sys
    #stdout, stderr = io.StringIO(), io.StringIO()
    command = [command] + [ f"--{k}={v}" for k,v in arguments.items() ] + fields_to_export
    print(f"Running: {' '.join(command)}")
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #proc.wait()
    
    # instead of proc.wait(), which could deadlock when the stdout buffer
    # is full, do this:
    stdout, stderr = "", ""
    while proc.poll() == None:
        stdout += proc.stdout.read()
        stderr += proc.stderr.read()
    stdout += proc.stdout.read()
    stderr += proc.stderr.read()
    #stdout, stderr = stdout.getvalue(), stderr.getvalue()
    if proc.returncode:
        print(stdout)
        print("STDERR:", stderr)
        raise ValueError(f"Could not execute '{command}'. Please run on the command line for inspection. Probably use gdb.")
    else:
        if return_ndarray:
            import io # builtin
            import numpy as np # external
            datafh = io.StringIO(stdout)
            data = np.genfromtxt(datafh, names=True)
            return data
        return stdout
