#!/usr/bin/env perl

my $before_name = $ARGV[0];
my $after_name  = $ARGV[1];

if ($#ARGV != 1) {
    printf("usage: report.pl <before> <after>\n");
}

open(BEFORE, $before_name) or die;
open(AFTER, $after_name) or die;

my %before = ();
my %after = ();

my $total_programs_before;

while (<BEFORE>) {
    my $line = $_;

    $line =~ /(.*):(.*)/;

    $before{$1} = $2;
    $total_programs_before++;
}

while (<AFTER>) {
    my $line = $_;

    $line =~ /(.*):(.*)/;

    $after{$1} = $2;
}

delete $before{"total"};
delete $after{"total"};

my $total_instructions_before = 0;
my $total_instructions_after = 0;
my $affected_programs_before = 0;
my $affected_instructions_before = 0;
my $affected_instructions_after = 0;

my %hurt_programs = ();

while (my ($prog, $before_count) = each(%before)) {
    my $after_count = $after{$prog};
    if ($after_count == "") {
	next;
    }

    $total_instructions_before += $before_count;
    $total_instructions_after += $after_count;

    if ($before_count == $after_count) {
	next;
    }

    if ($after_count > $before_count && $before_count != 0) {
	$hurt_programs{$prog} = $after_count / $before_count;
    }

    printf("%s: %4d -> %4d\n",
	   $prog, $before_count, $after_count);

    $affected_instructions_before += $before_count;
    $affected_instructions_after += $after_count;

    $affected_programs_before++;
}

printf("\n");

printf("Total instructions: %d -> %d\n",
       $total_instructions_before, $total_instructions_after);

printf("%d/%d programs affected (%.1f%%)\n",
       $affected_programs_before, $total_programs_before,
    100 * $affected_programs_before / $total_programs_before);

if ($affected_instructions_after < $affected_instructions_before) {
    printf("%d -> %d instructions in affected programs (%.1f%% reduction)\n",
	   $affected_instructions_before,
	   $affected_instructions_after,
	   100 - (100 * $affected_instructions_after /
		  $affected_instructions_before));
}

if ($affected_instructions_after > $affected_instructions_before) {
    printf("%d -> %d instructions in affected programs (%.1f%% increase)\n",
	   $affected_instructions_before,
	   $affected_instructions_after,
	   (100 * $affected_instructions_after /
	    $affected_instructions_before) - 100);
}

my $header = 0;

if (keys(%hurt_programs) != 0) {
    printf("hurt programs:\n");
    my @names = keys %hurt_programs;
    my @sorted = sort {
	$hurt_programs{$a} <=> $hurt_programs{$b}
    } @names;

    foreach (@sorted) {
	printf("%s: %.02f%%\n", $_, $hurt_programs{$_} * 100 - 100);
    }
}
