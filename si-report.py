#!/usr/bin/env python
# vim: set expandtab tabstop=4 softtabstop=4 shiftwidth=4: */
#
# Copyright 2015 Advanced Micro Devices, Inc.
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
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

from collections import defaultdict
import itertools
import re
import sys

def format_float(f, suffix = ' %'):
    return "{0:0.2f}{1}".format(f, suffix)

def get_str(value, suffix = ' %'):
    if type(value) == float:
        return format_float(value, suffix)
    else:
        return value

def calculate_percent_change(b, a):
    if b == 0:
        return 0
    return 100 * float(a - b) / float(b)

def cmp_max_unit(current, comp):
    return comp[0] > current[0]

def cmp_min_unit(current, comp):
    return comp[0] < current[0]

def cmp_max_per(current, comp):
    return calculate_percent_change(comp[1], comp[2]) > calculate_percent_change(current[1], current[2])

def cmp_min_per(current, comp):
    return calculate_percent_change(comp[1], comp[2]) < calculate_percent_change(current[1], current[2])

class si_stats:
    metrics = [
        ('sgprs', 'SGPRS', ''),
        ('vgprs', 'VGPRS', ''),
        ('spilled_sgprs', 'Spilled SGPRs', ''),
        ('spilled_vgprs', 'Spilled VGPRs', ''),
        ('code_size', 'Code Size', 'bytes'),
        ('lds', 'LDS', 'blocks'),
        ('scratch', 'Scratch', 'bytes per wave'),
        ('maxwaves', 'Max Waves', ''),
        ('waitstates', 'Wait states', ''),
    ]

    def __init__(self):
        self.error = False

        for name in self.get_metrics():
            self.__dict__[name] = 0

        self._minmax_testname = {}

    def copy(self):
        copy = si_stats()
        copy.error = self.error

        for name in self.get_metrics():
            copy.__dict__[name] = self.__dict__[name]

        copy._minmax_testname = self._minmax_testname.copy()

        return copy

    def to_string(self, suffixes = True):
        strings = []
        for name, printname, suffix in si_stats.metrics:
            string = "{}: {}".format(printname, get_str(self.__dict__[name]))

            if suffixes and len(suffix) > 0:
                string += ' ' + suffix

            minmax_testname = self._minmax_testname.get(name)
            if minmax_testname is not None:
                string += ' (in {})'.format(minmax_testname)

            strings.append(string + '\n')
        return ''.join(strings)

    def get_metrics(self):
        return [m[0] for m in si_stats.metrics]

    def __str__(self):
        return self.to_string()

    def add(self, other):
        for name in self.get_metrics():
            self.__dict__[name] += other.__dict__[name]

    def update(self, comp, cmp_fn, testname):
        for name in self.get_metrics():
            current = self.__dict__[name]
            if type(current) != tuple:
                current = (0, 0, 0)
            if cmp_fn(current, comp.__dict__[name]):
                self.__dict__[name] = comp.__dict__[name]
                self._minmax_testname[name] = testname

    def update_max(self, comp):
        for name in self.get_metrics():
            current = self.__dict__[name]
            if type(current) == tuple:
                current = self.__dict__[name][0]
            if comp.__dict__[name][0] > current:
                self.__dict__[name] = comp.__dict__[name]

    def update_min(self, comp):
        for name in self.get_metrics():
            current = self.__dict__[name]
            if type(current) == tuple:
                current = self.__dict__[name][0]
            if comp.__dict__[name][0] < current:
                self.__dict__[name] = comp.__dict__[name]

    def update_increase(self, comp):
        for name in self.get_metrics():
            if comp.__dict__[name][0] > 0:
                self.__dict__[name] += 1

    def update_decrease(self, comp):
        for name in self.get_metrics():
            if comp.__dict__[name][0] < 0:
                self.__dict__[name] += 1

    def is_empty(self):
        for name in self.get_metrics():
            x = self.__dict__[name]
            if type(x) == tuple and x[0] is not 0:
                return False
            if type(x) != tuple and x is not 0:
                return False
        return True


class si_parser(object):
    re_stats = re.compile(
        r"^Shader Stats: SGPRS: ([0-9]+) VGPRS: ([0-9]+) Code Size: ([0-9]+) "+
        r"LDS: ([0-9]+) Scratch: ([0-9]+) Max Waves: ([0-9]+) Spilled SGPRs: "+
        r"([0-9]+) Spilled VGPRs: ([0-9]+)")
    re_nop = re.compile("^\ts_nop ([0-9]+)")

    def __init__(self):
        self._stats = None
        self._in_disasm = False

    def finish(self):
        return self._stats

    def parse(self, msg):
        if not self._in_disasm:
            if msg == "Shader Disassembly Begin":
                old_stats = self._stats
                self._stats = si_stats()
                self._in_disasm = True
                return old_stats

            match = si_parser.re_stats.match(msg)
            if match is not None:
                if self._stats == None:
                    self._stats = si_stats()
                self._stats.sgprs = int(match.group(1))
                self._stats.vgprs = int(match.group(2))
                self._stats.spilled_sgprs = int(match.group(7))
                self._stats.spilled_vgprs = int(match.group(8))
                self._stats.code_size = int(match.group(3))
                self._stats.lds = int(match.group(4))
                self._stats.scratch = int(match.group(5))
                self._stats.maxwaves = int(match.group(6))
                old_stats = self._stats
                self._stats = None
                return old_stats

            if msg == "LLVM compile failed":
                old_stats = self._stats
                self._stats = None

                if old_stats is None:
                    old_stats = si_stats()
                old_stats.error = True
                return old_stats
        else:
            if msg == "Shader Disassembly End":
                self._in_disasm = False
                return None

            match = si_parser.re_nop.match(msg)
            if match:
                self._stats.waitstates += 1 + int(match.groups()[0])
                return None

def get_results(filename):
    """
    Returns a dictionary that maps shader_test names to lists of si_stats
    (corresponding to the different shaders within the test's programs).
    """
    results = defaultdict(list)
    parsers = defaultdict(si_parser)

    with open(filename, "r") as file:
        re_line = re.compile(r"^(.+\.shader_test) - (.*)$")

        for line in file:
            match = re_line.match(line)
            if match is None:
                continue

            name = match.group(1)
            message = match.group(2)

            stats = parsers[name].parse(message)
            if stats is not None:
                results[name].append(stats)

    for name, parser in parsers.items():
        stats = parser.finish()
        if stats is not None:
            print "Results for", name, "not fully parsed!"
            results[name].append(stats)

    return results


def compare_stats(before, after):
    result = si_stats()
    for name in result.get_metrics():
        b = before.__dict__[name]
        a = after.__dict__[name]
        result.__dict__[name] = (a - b, b, a)
    return result

def divide_stats(num, div):
    result = si_stats()
    for name in result.get_metrics():
        if div.__dict__[name] == 0:
            result.__dict__[name] = num.__dict__[name]
        else:
            result.__dict__[name] = 100.0 * float(num.__dict__[name]) / float(div.__dict__[name])
    return result

def print_before_after_stats(before, after, divisor = 1):
    result = si_stats()
    for name in result.get_metrics():
        b = before.__dict__[name] / divisor
        a = after.__dict__[name] / divisor
        if b == 0:
            percent = format_float(0.0)
        else:
            percent = format_float(100 * float(a - b) / float(b))
        result.__dict__[name] = '{} -> {} ({})'.format(get_str(b,''), get_str(a,''), percent)

    print result

def print_cmp_stats(comp):
    result = comp.copy()
    for name in result.get_metrics():
        if type(result.__dict__[name]) != tuple:
            a = 0
            b = 0
        else:
            b = result.__dict__[name][1]
            a = result.__dict__[name][2]
        if b == 0:
            percent = format_float(0.0)
        else:
            percent = format_float(100 * float(a - b) / float(b))
        result.__dict__[name] = '{} -> {} ({})'.format(get_str(b,''), get_str(a,''), percent)

    print result


def print_count(stats, divisor):
    result = si_stats()
    for name in result.get_metrics():
        count = stats.__dict__[name]
        percent = float(count) / float(divisor)
        result.__dict__[name] = '{} ({})'.format(get_str(count,''), get_str(percent))
    print result.to_string(False)

def compare_results(before_all_results, after_all_results):
    total_before = si_stats()
    total_after = si_stats()
    total_affected_before = si_stats()
    total_affected_after = si_stats()
    increases = si_stats()
    decreases = si_stats()
    max_increase_per = si_stats()
    max_decrease_per = si_stats()
    max_increase_unit = si_stats()
    max_decrease_unit = si_stats()

    num_affected = 0
    num_tests = 0
    num_shaders = 0
    num_after_errors = 0
    num_before_errors = 0

    all_names = set(itertools.chain(before_all_results.keys(), after_all_results.keys()))

    only_after_names = []
    only_before_names = []
    count_mismatch_names = []
    errors_names = []

    for name in all_names:
        before_test_results = before_all_results.get(name)
        after_test_results = after_all_results.get(name)

        if before_test_results is None:
            only_after_names.append(name)
            continue
        if after_test_results is None:
            only_before_names.append(name)
            continue

        if len(before_test_results) != len(after_test_results):
            count_mismatch_names.append(name)

        num_tests += 1
        have_error = False

        for before, after in zip(before_test_results, after_test_results):
            if before.error:
                num_before_errors += 1
            if after.error:
                num_after_errors += 1
            if after.error or before.error:
                have_error = True
                continue

            total_before.add(before)
            total_after.add(after)
            num_shaders += 1

            comp = compare_stats(before, after)
            if not comp.is_empty():
                num_affected += 1
                total_affected_before.add(before)
                total_affected_after.add(after)
                increases.update_increase(comp)
                decreases.update_decrease(comp)
                max_increase_per.update(comp, cmp_max_per, name)
                max_decrease_per.update(comp, cmp_min_per, name)
                max_increase_unit.update(comp, cmp_max_unit, name)
                max_decrease_unit.update(comp, cmp_min_unit, name)

        if have_error:
            errors_names.append(name)

    print '{} shaders in {} tests'.format(num_shaders, num_tests)
    if num_shaders == 0:
        return

    print "Totals:"
    print_before_after_stats(total_before, total_after)
    print "Totals from affected shaders:"
    print_before_after_stats(total_affected_before, total_affected_after)
    print "Increases:"
    print_count(increases, num_shaders)
    print "Decreases:"
    print_count(decreases, num_shaders)

    print "*** BY PERCENTAGE ***\n"
    print "Max Increase:\n"
    print_cmp_stats(max_increase_per)
    print "Max Decrease:\n"
    print_cmp_stats(max_decrease_per)

    print "*** BY UNIT ***\n"
    print "Max Increase:\n"
    print_cmp_stats(max_increase_unit)
    print "Max Decrease:\n"
    print_cmp_stats(max_decrease_unit)

    def report_ignored(names, what):
        if names:
            print "*** {} are ignored:".format(what)
            s = ', '.join(names[:5])
            if len(names) > 5:
                s += ', and {} more'.format(len(names) - 5)
            print s

    report_ignored(only_after_names, "Tests only in 'after' results")
    report_ignored(only_before_names, "Tests only in 'before' results")
    report_ignored(count_mismatch_names, "Tests with different number of shaders")
    report_ignored(errors_names, "Shaders with compilation errors")
    if num_after_errors > 0 or num_before_errors > 0:
        print "*** Compile errors encountered! (before: {}, after: {})".format(
            num_before_errors, num_after_errors)

def main():
    before = sys.argv[1]
    after = sys.argv[2]

    compare_results(get_results(before), get_results(after))

if __name__ == "__main__":
    main()
