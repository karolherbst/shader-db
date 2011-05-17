#!/usr/bin/env perl

$env = "env INTEL_DEBUG=wm";
$glslparsertest = "/home/anholt/src/piglit/bin/glslparsertest";

my $total = 0;
foreach my $filename (@ARGV) {
    $output = `$env $glslparsertest $filename pass 2> /dev/null`;

    my $count = 0;
    foreach my $line (split(/\n/, $output)) {
	if ($line =~ /align1/) {
	    $count++;
	}
    }
    printf("$filename: $count\n");

    $total += $count;
}
printf("total: $total\n");
