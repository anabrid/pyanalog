#!/usr/bin/perl

#
#  dda2c.pl implements a very simple "compiler" accepting the definition of a particular DDA-setup and 
# generating C-code which effectively implements the DDA. This program is normally called via simulate.pl
# and is not intended to be run in standalone-mode.
#
# 16-JUN-2018   B. Ulmann   Changed integrator and summer to implicit sign inversion
#                           Integrators now accept arbitrarily many input values
# 04-FEB-2020   B. Ulmann   Added sin/cos functions.
#

use strict;
use warnings;
use Data::Dumper;

my $debug = 0;               # Set to something not equal 0 to get some debug output
my $default_type = 'double'; # Default data type for calculations
my $int_scratch_number = 6;  # Number of scratch variables for the integration

die "Usage: dda2c.pl <dda_file> <steps> <modulus> <variables_to_be_plotted>\n" if @ARGV < 3;

my ($source, $steps, $modulus, @plot) = (@ARGV);
die "Modulus must be int >= 1, but is >>$modulus<<!\n" if $modulus < 1;
(my $destination = $source) =~ s/\./_/g;
$destination .= '.c';

my $time_and_date = localtime();

open my $source_fh, '<', $source or die "Could not open $source: $!\n";

my ($line_counter, @statements) = 0;
while (my $line = <$source_fh>) {
  $line_counter++;
  chomp($line);
  $line =~ s/#.*$//;
  $line =~ s/^\s+//;
  next unless $line;
  $line =~ s/\s+//g;

  # The following parser has been written by my friend Thomas Kratz 
  # whom I would like to thank for this beautiful piece of code. :-)

  my @S;
  my $i = 0;

  $S[$i++] = $1 while $line =~ s/
    (         # capture start
    \w+       # word chars
    \(        # opening parenthesis
    [^()]+    # no parens
    \)        # closing parenthesis
    )         # capture end
  /__S${i}_${line_counter}/x;     # replace __Sn

  # re-replace last element
  $i--;
  $line =~ s/__S${i}_${line_counter}/pop @S/e;

  # output of compiled elementary functions
  push(@statements, $line);
  push(@statements, "__S${_}_$line_counter=$S[$_]") for ( 0 .. $#S ) 

  # End of Thomas' code
}
close($source_fh);

my (%constants, %initial_values, %variables);
for my $i (0 .. @statements - 1) {
  my ($name, $value) = split('=', $statements[$i]);
  if ($value =~ m/^const\(/) { # static constant function
    die "Constant already defined: $statements[$i]\n" if $constants{$name};
    ($constants{$name}) = $value =~ m/^const\((.+)\)$/;
    $statements[$i] = '';
  } elsif ($value =~ m/^int\(/) { # integrate function - last parameter is I.C.
    die "Initial value already defined: $statements[$i]" 
        if $initial_values{$name};
    $value =~ s/^(int\(.+,.+),(.+)\)$/$1\)/; # Remove last parameter
    $initial_values{$name} = -$2;
    $statements[$i] = "$name=$value";
  } else { # dynamic function - remains in @statements
    die "Variable already defined: $statements[$i]\n" if $variables{$name};
    $variables{$name} = 1; # Just remember the variable
  }
}

print Dumper(\%constants, \%initial_values, \@statements) if $debug;

open my $destination_fh, '>', $destination or die "Could not open $destination: $!\n";

print $destination_fh "
/*
** Program name           : $destination
** Program source         : $source
** Time of compilation    : $time_and_date
** Variables to be plotted: ", join(', ', @plot), "
** Modulus:               : $modulus
*/

#include <stdio.h>
#include <math.h>

#include \"dda.h\"

int main() {
  /* Constant declarations */
";

# Write constant definitions
print $destination_fh "  $default_type $_ = $constants{$_};\n" 
    for (sort(keys(%constants)));

# Write initial value definitions
print $destination_fh "\n  /* Initial value definitions */\n";
print $destination_fh "  $default_type $_ = $initial_values{$_};\n" 
    for (sort(keys(%initial_values)));

#----
print $destination_fh "\n  /* Scratch variables */\n";
print $destination_fh "  $default_type __dyold_${_}[$int_scratch_number] = {",
      join(', ', split(/\./, '0.' x $int_scratch_number)), "};\n" 
    for (sort(keys(%initial_values)));
#----

# Write variable definitions
print $destination_fh "\n  /* Variable definitions */\n";
print $destination_fh "  $default_type $_ = 0.;\n" for (sort(keys(%variables)));

# Write actual program
print $destination_fh "
  /* Auxiliary variable definitions */
  unsigned int __i;

  /* Integration loop */
  for (__i = 0; __i < $steps; __i++) {
";

# Write operations to be performed to destination file
for my $statement (@statements) {
  next unless $statement;
  my ($result, $function, $arguments) = $statement =~ m/^(\w+)=(\w+)\((.+)\)$/;

  my $compiled_statement;
  my @argument_list = split(',', $arguments);

  if ($function eq 'neg') { # 1 argument
    die "Wrong number of arguments for 'neg': $statement\n" if @argument_list != 1;
    $compiled_statement = "$result = -$argument_list[0]";
  } elsif ($function eq 'sin') { # 1 argument
    die "Wrong number of arguments for 'sin': $statement\n" if @argument_list != 1;
    $compiled_statement = "$result = sin($argument_list[0])";
  } elsif ($function eq 'cos') { # 1 argument
    die "Wrong number of arguments for 'cos': $statement\n" if @argument_list != 1;
    $compiled_statement = "$result = cos($argument_list[0])";
  } elsif ($function eq 'div') { # 2 arguments
    die "Wrong number of arguments for 'div': $statement\n" if @argument_list != 2;
    $compiled_statement = "$result = $argument_list[0] / $argument_list[1]";
  } elsif ($function eq 'int') { # n arguments
    my $input = join('+', @argument_list[0 .. @argument_list - 2]);
    my $ivar  = $argument_list[-1];
    $compiled_statement = "__integrate(&$result, $input, $ivar, __dyold_$result);";
  } elsif ($function eq 'sum') { # n arguments
    die "Wrong number of arguments for 'sum': $statement\n" if @argument_list < 2;
    $compiled_statement = "$result = -(" . join(' + ', @argument_list) . ')';
  } elsif ($function eq 'mult') { # n arguments
    die "Too few of arguments for 'mult': $statement\n" if @argument_list < 2;
    $compiled_statement = "$result = " . join(' * ', @argument_list);
  } elsif ($function eq 'dead_upper') { # 2 arguments
    die "Wrong number of arguments for 'dead_upper': $statement\n" if @argument_list != 2;
    $compiled_statement = "$result = $argument_list[0] > $argument_list[1] ? $argument_list[0] - $argument_list[1] : 0.";
  } elsif ($function eq 'dead_lower') { # 2 arguments
    die "Wrong number of arguments for 'dead_lower': $statement\n" if @argument_list != 2;
    $compiled_statement = "$result = $argument_list[0] < $argument_list[1] ? $argument_list[0] - $argument_list[1] : 0.";
  } elsif ($function eq 'min') { # 2 arguments
    die "Wrong number of arguments for 'min': $statement\n" if @argument_list != 2;
    $compiled_statement = "$result = $argument_list[0] < $argument_list[1] ? $argument_list[0] : $argument_list[1]";
  } elsif ($function eq 'max') { # 2 arguments
    die "Wrong number of arguments for 'max': $statement\n" if @argument_list != 2;
    $compiled_statement = "$result = $argument_list[0] > $argument_list[1] ? $argument_list[0] : $argument_list[1]";
  } elsif ($function eq 'lt') { # 4 arguments
    die "Wrong number of arguments for 'lt': $statement\n" if @argument_list != 4;
    $compiled_statement = "$result = $argument_list[0] < $argument_list[1] ? $argument_list[2] : $argument_list[3]";
  } elsif ($function eq 'le') { # 4 arguments
    die "Wrong number of arguments for 'le': $statement\n" if @argument_list != 4;
    $compiled_statement = "$result = $argument_list[0] <= $argument_list[1] ? $argument_list[2] : $argument_list[3]";
  } elsif ($function eq 'gt') { # 4 arguments
    die "Wrong number of arguments for 'gt': $statement\n" if @argument_list != 4;
    $compiled_statement = "$result = $argument_list[0] > $argument_list[1] ? $argument_list[2] : $argument_list[3]";
  } elsif ($function eq 'ge') { # 4 arguments
    die "Wrong number of arguments for 'ge': $statement\n" if @argument_list != 4;
    $compiled_statement = "$result = $argument_list[0] >= $argument_list[1] ? $argument_list[2] : $argument_list[3]";
  } elsif ($function eq 'sqrt') { # 1 argument
    die "Wrong number of arguments for 'sqrt': $statement\n" if @argument_list != 1;
    $compiled_statement = "$result = sqrt($argument_list[0])";
  } elsif ($function eq 'abs') { # 1 argument
    die "Wrong number of arguments for 'abs': $statement\n" if @argument_list != 1;
    $compiled_statement = "$result = fabs($argument_list[0])";
  } elsif ($function eq 'floor') { # 1 argument
    die "Wrong number of arguments for 'floor': $statement\n" if @argument_list != 1;
    $compiled_statement = "$result = (int)($argument_list[0])";
  } else {
    die "Unknown function encountered: $statement\n";
  }

  print $destination_fh "    $compiled_statement;\n";
}

print $destination_fh "
    /* Write results to stdout */
    if (!(__i % $modulus))
        printf(\"", (map{'%.12g '}(@plot)), "\\n\", ", join(', ', @plot),");
  }

  return 0;
}
";
close($destination_fh);
