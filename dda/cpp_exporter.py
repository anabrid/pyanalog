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

For the C++ runtime arguments, we support so far:

- *Simulation steering*: Selection of number of integration iterations
  and frequency of dumping the solution.
- *Query based plotting*: Selection which variables shall be outputted
  at runtime.
- Further *Flags* and *Numeric arguments* as well as a useful ``--help``
  message.
- *Initial data* and *time step sizes* can also be chosen at run time.
- *Introspection capabilities*, for instance one can ask the binary
  about the evolution quantities built in.

Basically the equation structure is the only thing left hardcoded at
C++ code generation time.

"""

from . import clean
from .ast import State, Symbol, topological_sort
from .computing_elements import cpp_impl

# could also say is_number = lambda obj: str(obj).is_digit()
is_number = lambda obj: isinstance(obj, float) or isinstance(obj, int)

import textwrap, itertools, math, functools, os

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
    %(diff_or_integrate)s
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
// Originally, in this code, they just have been constexprs.
// For some applications, it is useful to have them being runtime arguments. This has to
// be chosen at code generation time, they are then compile time constants.
#define %(const_type)s_is_really_const %(constexpr_consts)d
static %(const_type_qualifier)s struct %(const_type)s {
    %(explicit_constant_definitions)s
    %(const_type_qualifier)s double* byName(std::string %(lookup_name)s) %(const_type_qualifier)s {
        %(explicit_constants_by_name)s
        return nullptr;
    }
} %(const_name)s;

%(explicit_constant_initializations)s

// All variables, time evolveds, constants, as well-ordered strings:
%(all_variables_as_string)s

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
    
// not used:
// bool
//    shall_differentiate{ %(differentiate_data)s };
    
%(state_type)s integrate(%(state_type)s& %(state_name)s, %(aux_type)s& %(aux_name)s, int rk_order) {
    %(state_type)s k1, k2, k3, k4;
    %(state_type)s updated;

    switch(rk_order) {
        case 1:
            // Explicit Euler scheme
            f(%(state_name)s, k1, %(aux_name)s);
            updated = %(state_name)s + k1*dt;
            break;
        case 2:
            // RK2 scheme
            f(%(state_name)s, k1, %(aux_name)s);
            f(%(state_name)s + k1*dt, k2, %(aux_name)s);
            updated = %(state_name)s + (k1+k2)*dt*0.5;
            break;
        case 3:
            // Kutta's third order scheme 
            f(%(state_name)s, k1, %(aux_name)s);
            f(%(state_name)s + dt*k1*0.5, k2, %(aux_name)s);
            f(%(state_name)s + dt*k1*(-1.0) + dt*k2*2.0, k3, %(aux_name)s);
            updated = %(state_name)s + (k1 + k2*4.0 + k3*1.0)*dt*(1./6.);
            break;
        case 4:
            // Classical RK4 scheme 
            f(%(state_name)s, k1, %(aux_name)s);
            f(%(state_name)s + dt*k1*0.5, k2, %(aux_name)s);
            f(%(state_name)s + dt*k2*0.5, k3, %(aux_name)s);
            f(%(state_name)s + dt*k3*1.0, k4, %(aux_name)s);
            updated = %(state_name)s + (k1 + k2*2.0 + k3*2.0 + k4)*dt*(1./6.);
            break;
        default:
            exit(-42);
    }
    
    return updated;
}

struct csv_writer {
    std::vector<std::string> query_variables;
    bool write_initial_conditions, always_compute_aux_before_printing, binary_output, skip_header;

    const char* sep(size_t i) const { return (i!=query_variables.size() ? "\\t" : "\\n"); }
    
    void write_header() const {
        if(binary_output || skip_header) return;
        for(size_t i=0; i<query_variables.size();)
            std::cout << query_variables[i++] << sep(i);
    }
    
    void write_line(const %(state_type)s& %(state_name)s, const %(aux_type)s& %(aux_name)s, %(const_type_qualifier)s %(const_type)s& %(const_name)s) const {
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

%(state_type)s simulate_dda(%(state_type)s initial, int max_iterations, int modulo_writer, int rk_order, int modulo_progress) {
    %(state_type)s %(state_name)s = initial, old = initial;
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
        %(state_type)s integrated = integrate(%(state_name)s, %(aux_name)s, rk_order);
        
        %(aux_type)s dummy; %(state_type)s dqdt;
        f(%(state_name)s, dqdt, dummy); // etxra round for dqdt only neccessary for first timestep
        %(state_type)s differences = (dqdt + old*(-1.0)) / dt;
        
        old = dqdt;
        %(state_name)s = %(state_type)s::diff_or_integrate(integrated, differences);
            
        // TODO: Currently, differentiation is always first order forward
        //       in time. Could also do higher order.

        if(iter %% modulo_writer == 0)
            writer.write_line(%(state_name)s, %(aux_name)s, %(const_name)s);
            
        if(modulo_progress >= 0 && iter %% modulo_progress == 0) {
            fprintf(stderr, "%%.0d%%%%... ", 100*iter / max_iterations );
            fflush(stderr);
        }
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


#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char** argv) {
    // cstd rand 
    srand((unsigned int)time(NULL));


    // runtime-definable arguments and their values:
    
    map<string, int> numbers;
    numbers["modulo_write"] = 1;
    numbers["max_iterations"] = 100;
    numbers["rk_order"] = 1;
    numbers["number_precision"] = 5;
    numbers["modulo_progress"] = -1;
    
    map<string, bool> flags;
    flags["debug"] = false;
    flags["list_all_variables"] = false;
    flags["write_initial_conditions"] = false;
    flags["always_compute_aux_before_printing"] = true;
    flags["binary_output"] = false;
    flags["skip_header"] = false;

    // Our primitive argument processing:
    vector<string> args(argv + 1, argv + argc);
    for(auto arg : args) {
        if(arg == "--help") {
            string ind = "  ";
            cerr << "Usage: " << argv[0] << " [arguments] <variables_to_print>" << endl;
            cerr << "This is an ODE integrator generated by PyDDA." << endl << endl;
            cerr << "* Boolean arguments (Usage --foo or --foo=1 or --foo=0)" << endl;
            for(auto const& [key, val] : flags) cerr << ind << key << " (default value: " << val << ")" << endl;
            cerr << "* Numeric arguments: (Usage --foo=123)" << endl;
            for(auto const& [key, val] : numbers) cerr << ind << key << " (default value: " << val << ")" << endl;
            cerr << "* Overwrite initial conditions (initial data): (Usage --initial:foo=1.23)" << endl;
            for(auto const& key : all_%(state_type)s) cerr << ind << key << " (default value: " << *initial_data.byName(key) << ")" << endl;
            cerr << "* Overwrite (per-variable) time step size: (Usage --dt:foo=0.001 or even --dt:foo=1e-6)" << endl;
            for(auto const& key : all_%(state_type)s) cerr << ind << key << " (default value: " << *dt.byName(key) << ")" << endl;
            #if %(const_type)s_is_really_const == 0
            cerr << "* Overwrite (runtime) constants: (Usage --const:foo=1.23)" << endl;
            for(auto const& key : all_%(const_type)s) cerr << ind << key << " (default value: " << *%(const_name)s.byName(key) << ")" << endl;
            #else
            cerr << "* Overwrite constants: Not possible since compiled as compile time constants." << endl;
            #endif
            cerr << "* Query fields: (if none given, all are dumped)";
            for(size_t i=0; i<all_variables.size();) { cerr << endl << ind;
                for(size_t j=0;j<5 && i<all_variables.size();j++) cerr << all_variables[i++] << (i!=all_variables.size() ? ", " : ""); }
            cerr << endl << endl << "Exemplaric usage:" << endl;
            cerr << ind << argv[0] << " --foo=1 --bar=0 --baz=7 --ic:var1=0.5 --dt:var2=0.01 --const:something=42 var1 var2 var3" << endl;
            cerr << endl << "For more options and help, see the PyDDA code documentation at https://pyanalog.readthedocs.io/" << endl;
            exit(-1);
        }
        
        // TODO: Compress the following repetitive lines with some function.
        if(unprefix(arg, "--dt:")) {
            vector<string> splitted = split(arg);
            if(splitted.size() != 2) { cerr << "ERR: Usage: --dt:key=value"; exit(-2); }
            string key=splitted[0]; double value=extract<double>(splitted[1]);
            if(!dt.byName(key)) { cerr << "ERR: --dt:"<<key<<" is not a valid argument. Check with --help"; exit(-2); }
            *(const_cast<double*>(dt.byName(key))) = value;
        } else if(unprefix(arg, "--initial:")) {
            vector<string> splitted = split(arg);
            if(splitted.size() != 2) { cerr << "ERR: Usage: --initial:key=value"; exit(-2); }
            string key=splitted[0]; double value=extract<double>(splitted[1]);
            if(!initial_data.byName(key)) { cerr << "ERR: --initial:"<<key<<" is not a valid argument. Check with --help"; exit(-2); }
            *(const_cast<double*>(initial_data.byName(key))) = value;
        } else if(unprefix(arg, "--const:")) {
            vector<string> splitted = split(arg);
            if(splitted.size() != 2) { cerr << "ERR: Usage: --const:key=value"; exit(-2); }
            string key=splitted[0]; double value=extract<double>(splitted[1]);
            if(!%(const_name)s.byName(key)) { cerr << "ERR: --const:"<<key<<" is not a valid argument. Check with --help"; exit(-2); }
            #if %(const_type)s_is_really_const == 0
                *(%(const_name)s.byName(key)) = value;
            #else
                cerr << "ERR: Cannot overwrite compile time constant." << endl;
                cerr << "ERR: Regenerate code with constexpr_consts=True in order to use this feature." << endl;
                exit(-3);
            #endif
        } else if(unprefix(arg, "--")) {
            vector<string> splitted = split(arg);
            if(splitted.size() == 1) splitted.push_back("1"); // for the booleans
            if(splitted.size() != 2) {
                cerr << "ERR: Illegal key-value argument " << arg << endl;
                cerr << "ERR: Try --help" << endl;
                exit(-3);
            }
            string key=splitted[0], value=splitted[1];
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
    writer.skip_header = flags["skip_header"];
    
    simulate_dda(initial_data, numbers["max_iterations"], numbers["modulo_write"], numbers["rk_order"], numbers["modulo_progress"]);
}

"""

def to_cpp(state, number_precision=math.inf, constexpr_consts=False):
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

    state = clean(state, target="C").name_computing_elements()
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

    # HOTFIX rename reserved keywords in the C language
    # FIXME: Should have a better solution valid for *every* possible collision. 
    # C++ namespaces are apparently not enough.
    c_names = { "div": "Div", "abs": "Abs" }
    c_substitute = lambda head: c_names.get(head, head)
    state = State({ var: state[var].map_heads(c_substitute) for var in state })

    # Extract int(..., timestep, initial_data) and rewrite reserved C keyword
    # Also extract diff(..., timestep) and rewrite symbol
    timesteps = {}
    initial_data = {}
    differentiate = {}
    def map_and_treat_integrals(var):
        if not var in vars.evolved: return state[var]
        assert state[var].head in ["int", "diff"], f"Expected int(...) or diff(...) but got {state}"
        head, tail = state[var].head, state[var].tail
        if not len(tail) >= 3: raise ValueError(f"{head}(...) requires at least {head}(value, dt, initial_value)")
        timesteps[var] = lookup_const(tail[-2])
        initial_data[var] = lookup_const(tail[-1])
        differentiate[var] = head == "diff"
        return Symbol(head.capitalize(), *tail[0:len(tail)-2])
    state = State({ var: map_and_treat_integrals(var) for var in state })

    
    # do the renaming *after* variable dependency analysis
    state = state.map_tails(remove_const, map_root=False)
    state = state.map_tails(prefix_rhs,   map_root=False)
        
    # C-format lists of statements or so. Do indentation.
    J = lambda whatever: ", ".join(whatever)
    C = lambda whatever: textwrap.indent(whatever if isinstance(whatever, str) else  "\n".join(whatever), indent)
    CC = lambda whatevr: C(C(whatevr)) # two indentations ;-)
    Cw = lambda whatever: C(textwrap.wrap(whatever, width=50))
    enc = lambda ws, inner: ws[0] + inner + (ws[1] if len(ws)==2 else ws[0]) # enc('"','foo') or enc('{}','foo')
    varlist = lambda ctype, lst: Cw(f"{ctype} {', '.join(lst)};") if lst else ""

    state_var_definition = varlist("double", vars.evolved)
    aux_var_definition = varlist("double", vars.aux.all)
    
    # For runtime (i.e. CLI invocation) introspection capabilities
    lookup = lambda struct, prefix="": CC(f'if({lookup_name} == "{var}") return &{prefix}{var};' for var in struct)
    state_vars_by_name = lookup(vars.evolved)
    aux_vars_by_name = lookup(vars.aux.all)
    explicit_constants_by_name = lookup(vars.explicit_constants, prefix=const_type+"::")
    
    # For even more runtime (i.e. CLI invocation) introspection capabilities
    variable_namings = {
        "variables": vars.all,
        state_type:  vars.evolved,
        aux_type:    vars.aux.all,
        const_type:  vars.explicit_constants,
    }
    all_variables_as_string = varlist("static const std::vector<std::string>",
        ["all_"+k+" = "+enc("{}", Cw(', '.join([ enc('"',vi) for vi in v ])))
            for k,v in variable_namings.items() ]).lstrip()
    
    # the above replaces repepetitive stuff such as:
    #all_variables_as_string = C(f'"{var}",' for var in vars.all)
    #all_state_vars_by_name = C(f'"{var}",' for var in vars.evolved)
    #all_constants_by_name = C(f'"{var}",' for var in vars.explicit_constants)

    # For debugging:
    aux_var_set_to_nan = C(f"{var} = {nan_name};" for var in vars.aux.all)
    
    # Workaround for avoiding logic in template...
    either = lambda lst, otherwise: lst if lst else [otherwise]
    nonemptyvarlist = lambda lst: either(lst, otherwise="_none=-1")
    
    const_assignments = [f"{var}={state[var].tail[0]}" for var in vars.explicit_constants] # extract x in const(x)
    if constexpr_consts:
        const_type_qualifier = "const"
        # generates a member in const struct foo { constexpr static double bla = 1, blo = 2, ...; }
        explicit_constant_definitions = varlist("constexpr static double", nonemptyvarlist(const_assignments))
        explicit_constant_initializations = ""
    else:
        const_type_qualifier = ""
        # generates a member in struct foo { static double bla, blo, ...; }
        explicit_constant_definitions = varlist("static double", either(vars.explicit_constants, otherwise="_none"))
        # and subsequently foo::bla=1, foo::blo=2, ...
        explicit_constant_initializations = C(f"double {const_type}::{ass};" for ass in const_assignments)
    
    initial_data = J(str(initial_data[var]) for var in vars.evolved)
    timestep_data = J(str(timesteps[var]) for var in vars.evolved)
    
    diff_or_integrate = C([ \
        f"static {state_type} diff_or_integrate(const {state_type} &integrals, const {state_type} &difference) "+'{', \
        C(f"{state_type} {state_name};"), \
        C(f"{state_name}.{var} = {'difference' if differentiate[var] else 'integrals'}.{var};" for var in vars.evolved), \
        C(f"return {state_name};"), \
        "}"])
    
    # leftover/bookkeeping/better doing    
    differentiate_data = J(str(differentiate[var]) for var in vars.evolved)

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
        itertools.product("*+/", zip((state_type, "double"), (True,False,False))))

    output = cpp_template % {**locals(), **globals()}
    return output

# What follows are a few helper functions to make the usage nicer

default_c_filename = "generated.cc"
default_compiler_output = "./a.out"

def compile(code, c_filename=default_c_filename, compiler="g++", compiler_output=default_compiler_output, options="--std=c++17 -Wall"):
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

def runproc(command, decode=False):
    "Helper to run external command and slurp its output to a binary array"
    import subprocess # internals
    # Popen: Python 3.6 does not yet have the text keyword. Newer Pythons have.
    # We do a decode("utf-8") later for the same purpose.
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)#, stderr=subprocess.PIPE) # text=True)        
    # pass stderr to user for progress bar.
    (stdout,stderr) = proc.communicate()
    #stderr += proc.stderr.read()
    if decode:
        stdout = stdout.decode("utf-8")
        #stderr = stderr.decode("utf-8")
    return proc, stdout#, stderr

def list_all_variables(command=default_compiler_output):
    "in order to know which fields have been read, slurp all variables"
    fproc, fields = runproc([command, "--list_all_variables"], decode=True)
    if fproc.returncode:
        #warnings.warn("Could not extract evolution variables automagically from command: "+stderr+", Stdout: "+stdout)
        #warnings.warn("Could not extract evolution variables automagically from command (see stderr above). Stdout: "+stdout)
        raise ValueError("Could not extract evolution variables automagically from command (see stderr above). Stdout: "+stdout)
    else:
        fields_to_export = fields.strip().split("\n")
    return fields_to_export

def run(command=default_compiler_output, binary=False, arguments={}, fields_to_export=[]):
    """
    Small helper function to execute a code generated by this module.
    
    Runs ``command`` on the command line, with given dict ``arguments`` in ``--foo=bar``
    fashion and ``fields_to_export`` just as a sequential argument list. If no
    ``fields_to_export`` is given, ``command --list_all_variables`` will be run to query
    all default fields.
    
    Pipes stdout to a string, which is returned. Stderr will just be passed.
    The function will return once the binary finished or raise in case of error.
    
    If you set ``binary=True``, raw data instead of CSV files will be passed between the spawned
    command and this python program. This decreases the runtime significantly if you write a lot
    of data (since CSV generating and parsing overload is gone). 
    
    Example usage:
    
    >>> from dda import *
    >>> state = State()
    >>> state["x"] = Symbol("int", Symbol("neg", state["x"]), 0.2, 1)
    >>> state
    State({'x': int(neg(x), 0.2, 1)})
    >>> cpp_code = to_cpp(state)
    >>> print(cpp_code)  # doctest: +SKIP
    // This code was generated by PyDDA.
    #include <cmath> /* don't forget -lm for linking */
    #include <cfenv> /* for feraisexcept and friends */
    #include <limits> /* for signaling NAN */
    #include <vector>
    ....
    >>> compile(cpp_code, compiler_output="foo.exe")
    >>> res = run("./foo.exe", arguments={'max_iterations':10}, fields_to_export=['x']) # doctest: +SKIP
    Running: ./foo.exe --max_iterations=10 x
    TODO: Doctesting this doesn't work good due to stderr (cf https://stackoverflow.com/a/61533524)
    >>> print(res) # doctest: +NORMALIZE_WHITESPACE +SKIP
    x
    1.2
    1.44
    1.728
    2.0736
    2.48832
    2.98598
    3.58318
    4.29982
    5.15978
    6.19174


    """
    if binary: arguments["binary_output"] = 1
    command_with_args = [command] + [ f"--{k}={v}" for k,v in arguments.items() ] + fields_to_export
    print(f"Running: {' '.join(command_with_args)}")
    proc, stdout = runproc(command_with_args, decode=not binary)

    if proc.returncode:
        print(stdout)
        #print("STDERR:", stderr)
        raise ValueError(f"Could not execute '{command_with_args}'. Please run on the command line for inspection. Probably use gdb.")
    else:
        return stdout

def numpy_read(stdout, binary=False, return_ndarray=True, return_recarray=False, fields_to_export=[]):
    """
    Postprocessing to fill the gap between the C++ output and a suitable numpy array.
    In order to so, this function has to know whether your output was binary or text.
    Furthermore, you need to tell him how many fields you had. You can use :meth:`list_all_variables`
    
    Old Text:
    
    This option only makes real sense if
    you set (the default) ``return_ndarray=True``. Note that if you don't pass the  ``fields_to_export``
    option but set ``binary=True``, in the moment the returned array is one-dimensional (a warning
    will be printed). If you like even more structured data be returned, turn on ``return_recarray=True``.
    It will return a numpy.recarray, the same data type which you get when you read CSV data
    with column headers. ``return_recarray=True`` implies ``return_ndarray=True``.
    """
    if return_recarray:
        return_ndarray = True
    if return_ndarray:
        import warnings # bultin
        import numpy as np # external
        
        if binary:
            # note that `binary` will give you a long array of numbers instead of a two-dimensional array.
            # Any structural information is lacking and has to be introduced again.
            
            if not fields_to_export:
                raise ValueError("No fields given. Please pass fields_to_export=list_all_variables().")
            
            data = np.frombuffer(stdout, dtype="<f8")
            if fields_to_export:
                N = len(data) / len(fields_to_export)
                assert N.is_integer(), "1d number sequence from C run is not divisible by number of fields."
                data = data.reshape(int(N), len(fields_to_export))
                if return_recarray:
                    dt = [ (f, data.dtype) for f in fields_to_export ]
                    data = data.view(dt)  # this will be of shape (N,1)
                    data = data[:,0]      # strip this unneccessary extra axis!
            else:
                warnings.warn("Returning one-dimensional numpy array instead of a structured two-dimensional array. Pass fields_to_export=['foo','bar','baz'] in order to recieve two-dimensional array.")
                pass
        else:
            from io import StringIO
            if return_recarray:
                data = np.genfromtxt(StringIO(stdout), names=True)
            else:
                data = np.genfromtxt(StringIO(stdout), skip_header=1)
        return data
    else:
        return stdout

class Solver:
    """
    Syntactic sugar for a more concise OOP feeling. Instead of calling ``export(to="C")``,
    ``compile()`` and ``run()`` you can just write ``Solver(state, runtime_arguments)``.
    This object will even clean up after running.
    """
    def __init__(self, dda_state_or_code, *runtime_fields_to_export, constexpr_consts=True, **runtime_arguments):
        self.c_code = to_cpp(dda_state_or_code, constexpr_consts=constexpr_consts) if isinstance(dda_state_or_code, State) else dda_state_or_code
        
        self.code_name = "cpp_generated.cc"
        self.output_name = "cpp_generated.exe"
        self.default_runtime_fields_to_export = runtime_fields_to_export
        self.default_runtime_arguments = runtime_arguments
        
        compile(self.c_code, c_filename=self.code_name, compiler_output=self.output_name)
        
    def run(self, *runtime_fields_to_export, binary=False, cleanup=True, **runtime_arguments):
        "Chaining and Syntactic sugar for delayed argument setting/overwriting"
        self.runtime_arguments = { **runtime_arguments, **self.default_runtime_arguments }
        self.runtime_fields_to_export = list(runtime_fields_to_export if runtime_fields_to_export else self.default_runtime_fields_to_export)
        self.binary = binary
    
        self.stdout = run(command="./" + self.output_name, binary=self.binary,
                  arguments=self.runtime_arguments,
                  fields_to_export=self.runtime_fields_to_export)
        
        if self.binary and not self.runtime_fields_to_export:
            # Could also extract field values from dda state...
            self.fields = list_all_variables("./" + self.output_name)
        else:
            self.fields = self.runtime_fields_to_export
        
        if cleanup:
            os.unlink(self.code_name)
            os.unlink(self.output_name)
        return self # chainable!

    def as_ndarray(self):
        "Return run results as a ``np.ndarray`` (i.e. like a table without headers, typically 2D data)"
        if not hasattr(self, "stdout"): raise LogicError("First call run() on the simulator before data readout.")
        return numpy_read(self.stdout, binary=self.binary, return_ndarray=True, return_recarray=False, fields_to_export=self.fields)
        
    def as_recarray(self):
        "Return run results as a ``np.recarray`` (i.e. like CSV table with named headers)"
        if not hasattr(self, "stdout"): raise LogicError("First call run() on the simulator before data readout.")
        return numpy_read(self.stdout, binary=self.binary, return_ndarray=True, return_recarray=True,  fields_to_export=self.fields)
