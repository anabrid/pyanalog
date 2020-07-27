use strict;
use warnings;

BEGIN {push @INC, '../../HybridController/IO-HyCon/lib/'}

use IO::HyCon;
use POSIX;

my $ac = IO::HyCon->new();
$ac->setup('XBAR16');
$ac->single_run_sync();
$ac->get_data();
$ac->plot(terminal => "pdf", output => "output.pdf",
    title => strftime("%Y-%m-%d %H:%M:%S", localtime time),
    lines => [
    	"set yrange [-1.3:1.3]"    
    ]);
$ac->store_data(filename => 'result.dat');
