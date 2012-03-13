#!/usr/bin/env perl

$env = "env shader_precompile=true INTEL_DEBUG=wm,vs";
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
