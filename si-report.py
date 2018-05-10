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

set_red = "\033[31m"
set_green = "\033[1;32m"
set_yellow = "\033[1;33m"
set_normal = "\033[0m"

def format_float(f, suffix = ' %'):
    return "{0:0.2f}{1}".format(f, suffix)

def get_str(value, suffix = ' %'):
    if type(value) == float:
        return format_float(value, suffix)
    else:
        return value

def calculate_percent_change(b, a):
    if b == 0:
        return 0 if a == 0 else float("inf")
    return 100 * float(a - b) / float(b)

def format_table_cell(n, more_is_better = False, colored = True, is_percent = False):
    if is_percent and abs(n) < 0.01:
        return "     .    "

    str =  ("{:>8.2f} %" if is_percent else "{:>10}").format(n)
    if colored:
        if n > 0.5:
            str = (set_green if more_is_better else set_red) + str + set_normal
        elif n < -0.5:
            str = (set_red if more_is_better else set_green) + str + set_normal
    return str


def format_percent_change(b, a, more_is_better = False, colored = True):
    percent = calculate_percent_change(b, a)
    return format_table_cell(percent, more_is_better, colored, is_percent = True)

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
        ('privmem_vgprs', 'Private memory VGPRs', ''),
        ('scratch_size', 'Scratch size', 'dwords per thread'),
        ('code_size', 'Code Size', 'bytes'),
        ('lds', 'LDS', 'blocks'),
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
    re_stats = [
        re.compile(
            r"^Shader Stats: SGPRS: ([0-9]+) VGPRS: ([0-9]+) Code Size: ([0-9]+) "+
            r"LDS: ([0-9]+) Scratch: ([0-9]+) Max Waves: ([0-9]+) Spilled SGPRs: "+
            r"([0-9]+) Spilled VGPRs: ([0-9]+) PrivMem VGPRs: ([0-9]+)"),
        re.compile(
            r"^Shader Stats: SGPRS: ([0-9]+) VGPRS: ([0-9]+) Code Size: ([0-9]+) "+
            r"LDS: ([0-9]+) Scratch: ([0-9]+) Max Waves: ([0-9]+) Spilled SGPRs: "+
            r"([0-9]+) Spilled VGPRs: ([0-9]+)"),
    ]

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

            for re in si_parser.re_stats:
                match = re.match(msg)
                if match is not None:
                    break

            if match is not None:
                if self._stats == None:
                    self._stats = si_stats()
                self._stats.sgprs = int(match.group(1))
                self._stats.vgprs = int(match.group(2))
                self._stats.spilled_sgprs = int(match.group(7))
                self._stats.spilled_vgprs = int(match.group(8))
                self._stats.privmem_vgprs = int(match.group(9)) if match.lastindex >= 9 else 0
                self._stats.code_size = int(match.group(3))
                self._stats.lds = int(match.group(4))
                self._stats.scratch_size = int(match.group(5)) / (64 * 4)
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

def subtract_stats(x, y):
    result = si_stats()
    for name in result.get_metrics():
        result.__dict__[name] = x.__dict__[name] - y.__dict__[name]
    return result

def is_regression(before, after):
    for field in before.get_metrics():
        if field == 'maxwaves':
            if before.__dict__[field] > after.__dict__[field]:
                return True
        else:
            if before.__dict__[field] < after.__dict__[field]:
                return True
    return False

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

class grouped_stats:
    def __init__(self):
        self.num_shaders = 0
        self.before = si_stats()
        self.after = si_stats()
        self.diff = si_stats()

    def add(self, before, after):
        self.num_shaders += 1
        self.before.add(before)
        self.after.add(after)

    def set_one_shader(self, before, after):
        self.before = before
        self.after = after
        self.diff = subtract_stats(after, before)

    def print_vgpr_spilling_app(self, name):
        if (self.after.spilled_vgprs > 0 or
            self.after.privmem_vgprs > 0):
            print " {:6}{:6}     {:6}   {:6}   {:22}".format(
                self.num_shaders,
                self.after.spilled_vgprs,
                self.after.privmem_vgprs,
                self.after.scratch_size,
                name)

    def print_one_shader_vgpr_spill(self, name):
        if (self.after.spilled_vgprs > 0 or
            self.after.privmem_vgprs > 0):
            print " {:6}{:6}{:6}   {:6}    {:22}".format(
                self.after.vgprs,
                self.after.spilled_vgprs,
                self.after.privmem_vgprs,
                self.after.scratch_size,
                name)

    def print_sgpr_spilling_app(self, name):
        if self.after.spilled_sgprs > 0:
            print " {:6} {:6}     {:>5.1f}      {:22}".format(
                self.num_shaders,
                self.after.spilled_sgprs,
                float(self.after.spilled_sgprs) / float(self.num_shaders),
                name)

    def print_one_shader_sgpr_spill(self, name):
        if self.after.spilled_sgprs > 0:
            print " {:6}{:6}   {:90}".format(
                self.after.sgprs,
                self.after.spilled_sgprs,
                name)

    def print_percentages(self, name):
        print " {:6}{:6}{}{}{}{}{}{}{}{}{}".format(
            name,
            self.num_shaders,
            format_percent_change(self.before.sgprs, self.after.sgprs),
            format_percent_change(self.before.vgprs, self.after.vgprs),
            format_percent_change(self.before.spilled_sgprs, self.after.spilled_sgprs),
            format_percent_change(self.before.spilled_vgprs, self.after.spilled_vgprs),
            format_percent_change(self.before.privmem_vgprs, self.after.privmem_vgprs),
            format_percent_change(self.before.scratch_size, self.after.scratch_size),
            format_percent_change(self.before.code_size, self.after.code_size),
            format_percent_change(self.before.maxwaves, self.after.maxwaves, more_is_better = True),
            format_percent_change(self.before.waitstates, self.after.waitstates))

    def print_percentages_end(self, name):
        print " {:22}{:6}{}{}{}{}{}{}{}{}{}".format(
            name,
            self.num_shaders,
            format_percent_change(self.before.sgprs, self.after.sgprs),
            format_percent_change(self.before.vgprs, self.after.vgprs),
            format_percent_change(self.before.spilled_sgprs, self.after.spilled_sgprs),
            format_percent_change(self.before.spilled_vgprs, self.after.spilled_vgprs),
            format_percent_change(self.before.privmem_vgprs, self.after.privmem_vgprs),
            format_percent_change(self.before.scratch_size, self.after.scratch_size),
            format_percent_change(self.before.code_size, self.after.code_size),
            format_percent_change(self.before.maxwaves, self.after.maxwaves, more_is_better = True),
            format_percent_change(self.before.waitstates, self.after.waitstates))

    def print_regression(self, name, field):
        more_is_better = field == "maxwaves"
        print " {:6}{:6}{}{}   {:90}".format(
            self.before.__dict__[field],
            self.after.__dict__[field],
            format_table_cell(self.after.__dict__[field] - self.before.__dict__[field],
                              more_is_better = more_is_better),
            format_percent_change(self.before.__dict__[field], self.after.__dict__[field],
                                  more_is_better = more_is_better),
            name)

"""
Return "filename [index]", because files can contain multiple shaders.
"""
def get_shader_name(list, orig):
    for i in range(10):
        # add the index to the name
        name = orig + " [{}]".format(i)
        if name not in list:
                return name
    assert False
    return "(error)"


def print_yellow(str):
    print set_yellow + str + set_normal

def print_tables(before_all_results, after_all_results):
    re_app = re.compile(r"^.*/([^/]+)/[^/]+$")

    num_listed = 40
    apps = defaultdict(grouped_stats)
    shaders = defaultdict(grouped_stats)
    total = grouped_stats()
    total_affected = grouped_stats()

    all_files = set(itertools.chain(before_all_results.keys(),
                                    after_all_results.keys()))

    for file in all_files:
        # get the application name (inner-most directory)
        match_app = re_app.match(file)
        if match_app is None:
            app = "(unknown)"
        else:
            app = match_app.group(1)
        if len(app) > 22:
            app = app[0:19] + ".."

        before_test_results = before_all_results.get(file)
        after_test_results = after_all_results.get(file)

        if before_test_results is None or after_test_results is None:
            continue

        for before, after in zip(before_test_results, after_test_results):
            if after.error or before.error:
                continue

            apps[app].add(before, after)
            total.add(before, after)

            if not subtract_stats(before, after).is_empty():
                total_affected.add(before, after)

            # we don't have to add all shaders, just those that we may need
            # to display
            if (is_regression(before, after) or
                after.scratch_size > 0 or
                after.spilled_vgprs > 0 or
                after.privmem_vgprs > 0 or
                after.spilled_sgprs > 0):
                name = get_shader_name(shaders, file)
                shaders[name].set_one_shader(before, after)

    # worst VGPR spills
    num = 0
    sort_key = lambda v: -v[1].after.scratch_size
    for name, stats in sorted(shaders.items(), key = sort_key):
        if num == 0:
            print_yellow("WORST VGPR SPILLS (not deltas)" + (" " * 64))
            print_yellow("  VGPRs Spills Private Scratch")
        stats.print_one_shader_vgpr_spill(name)
        num += 1
        if num == num_listed:
            break
    if num > 0:
        print

    # VGPR spilling apps
    print_yellow("VGPR SPILLING APPS\nShaders SpillVGPR  PrivVGPR ScratchSize")
    for name, stats in sorted(apps.items()):
        stats.print_vgpr_spilling_app(name)
    print

    # worst SGPR spills
    num = 0
    sort_key = lambda v: -v[1].after.spilled_sgprs
    for name, stats in sorted(shaders.items(), key = sort_key):
        if num == 0:
            print_yellow("WORST SGPR SPILLS (not deltas)" + (" " * 64))
            print_yellow("  SGPRs Spills")
        stats.print_one_shader_sgpr_spill(name)
        num += 1
        if num == num_listed:
            break
    if num > 0:
        print

    # SGPR spilling apps
    print_yellow(" SGPR SPILLING APPS\nShaders SpillSGPR AvgPerSh")
    for name, stats in sorted(apps.items()):
        stats.print_sgpr_spilling_app(name)
    print

    # worst regressions
    metrics = si_stats().metrics
    for i in range(len(metrics)):
        field = metrics[i][0]
        num = 0
        more_is_better = metrics[i][0] == 'maxwaves'

        if more_is_better:
            sort_key = lambda v: v[1].diff.__dict__[field]
        else:
            sort_key = lambda v: -v[1].diff.__dict__[field]

        for name, stats in sorted(shaders.items(), key = sort_key):
            if more_is_better:
                if stats.diff.__dict__[field] >= 0:
                    continue
            else:
                if stats.diff.__dict__[field] <= 0:
                    continue

            if num == 0:
                print_yellow(" WORST REGRESSIONS - {:64}".format(metrics[i][1]))
                print_yellow(" Before After     Delta Percentage")
            stats.print_regression(name, field)
            num += 1
            if num == num_listed:
                break
        if num > 0:
            print
            stats.print_regression(name, field)
            num += 1
            if num == num_listed:
                break
        if num > 0:
            print

    # percentages
    legend = "Shaders     SGPRs     VGPRs SpillSGPR SpillVGPR  PrivVGPR   Scratch  CodeSize  MaxWaves     Waits"
    print_yellow(" PERCENTAGE DELTAS    " + legend)
    for name, stats in sorted(apps.items()):
        stats.print_percentages_end(name)
    print " " + ("-" * (21 + len(legend)))
    total_affected.print_percentages_end("All affected")
    print " " + ("-" * (21 + len(legend)))
    total.print_percentages_end("Total")
    print

def main():
    before = sys.argv[1]
    after = sys.argv[2]

    results_before = get_results(before)
    results_after = get_results(after)

    compare_results(results_before, results_after)
    print_tables(results_before, results_after)

if __name__ == "__main__":
    main()
