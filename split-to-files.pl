#!/usr/bin/env perl

my $appname = $ARGV[0];
my $log = $ARGV[1];

if ($#ARGV != 1) {
    printf("usage: split-to-files.pl <appname> <log>\n");
}

mkdir("shaders/$appname");

open(LOG, $log) or die;

my $vert_index = 1;
my $frag_index = 1;

while (<LOG>) {
    my $line = $_;
    if ($line =~ /GLSL source for vertex shader/) {
	open(OUT, ">shaders/$appname/$vert_index.vert");
	$vert_index++;
    } elsif ($line =~ /GLSL source for fragment shader/) {
	open(OUT, ">shaders/$appname/$frag_index.frag");
	$frag_index++;
    } elsif ($line =~ /IR for linked/) {
	close(OUT);
    } elsif ($line =~ /IR for shader/) {
	close(OUT);
    } else {
	print OUT $line;
    }
}
close $fh;
