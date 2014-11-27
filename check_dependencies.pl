#!/usr/bin/perl
#
# Copyright © 2014 Intel Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the next
# paragraph) shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

# For checking that shader_test's dependencies are correct.
#
# Run with
# 	./check_dependencies.pl shaders/
#
# And then run a command like these to add dependencies to the [require]
# section:
#
# find shaders/ -name '*.shader_test' -exec grep -l '#version 120' {} + | xargs sed -i -e 's/GLSL >= 1.10/GLSL >= 1.20/'
# find shaders/ -name '*.shader_test' -exec grep -l '#extension GL_ARB_texture_rectangle : require' {} + | xargs sed -i -e 's/GLSL >= 1.20/GLSL >= 1.20\nGL_ARB_texture_rectangle/'

use strict;
use File::Find;

die("Not enough arguments: specify a directory\n") if ($#ARGV < 0);

# The array_diff function is copied from the Array::Utils package and contains
# this copyright:
#
# This module is Copyright (c) 2007 Sergei A. Fedorov.
# All rights reserved.
#
# You may distribute under the terms of either the GNU General Public
# License or the Artistic License, as specified in the Perl README file.
sub array_diff(\@\@) {
	my %e = map { $_ => undef } @{$_[1]};
	return @{[ ( grep { (exists $e{$_}) ? ( delete $e{$_} ) : ( 1 ) } @{ $_[0] } ), keys %e ] };
}

my @shader_test;

sub wanted {
	push(@shader_test, $File::Find::name) if (/\.shader_test$/);
}

finddepth(\&wanted,  @ARGV);

foreach my $shader_test (@shader_test) {
	my $expected;
	my $actual;
	my @expected_ext;
	my @actual_ext;

	open(my $fh, "<", $shader_test)
		or die("cannot open < $shader_test: $!\n");
	
	while (<$fh>) {
		chomp;

		if (/^GLSL >= (\d)\.(\d\d)/) {
			$expected = $1 * 100 + $2;
		}
		if (/^\s*#\s*version\s+(\d{3})/) {
			$actual = $1 if $actual == undef;
			$actual = $1 if $actual < $1;
		}

		if (/^(GL_\S+)/) {
			next if ($1 eq "GL_ARB_fragment_program" ||
				 $1 eq "GL_ARB_vertex_program");
			push(@expected_ext, $1);
		}
		if (/^\s*#\s*extension\s+(GL_\S+)\s*:\s*require/) {
			push(@actual_ext, $1);
		}
	}

	close($fh);

	if ($actual != undef && $expected != $actual) {
		print "$shader_test requested $expected, but requires $actual\n"
	}

	my @extension = array_diff(@expected_ext, @actual_ext);
	foreach my $extension (@extension) {
		print "$shader_test extension $extension mismatch\n";
	}
}
