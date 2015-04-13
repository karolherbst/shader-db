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

import re
import sys

def format_float(f, suffix = ' %'):
    return "{0:0.2f}{1}".format(f, suffix)

def get_str(value, suffix = ' %'):
    if type(value) == float:
        return format_float(value, suffix)
    else:
        return value

def get_value_str(value, prefix, suffix):
    space = ' '
    if len(suffix) == 0:
        space = ''
    return "{}: {}{}{}\n".format(prefix, get_str(value), space, suffix)

def get_sgpr_str(value, suffixes = True):
    return get_value_str(value, 'SGPRS', '')

def get_vgpr_str(value, suffixes = True):
    return get_value_str(value, 'VGPRS', '')

def get_code_size_str(value, suffixes = True):
    suffix = ''
    if suffixes:
        suffix = 'bytes'
    return get_value_str(value, 'Code Size', suffix)

def get_lds_str(value, suffixes = True):
    suffix = ''
    if suffixes:
        suffix = 'blocks'
    return get_value_str(value, 'LDS', suffix)

def get_scratch_str(value, suffixes = True):
    suffix = ''
    if suffixes:
        suffix = 'bytes per wave'
    return get_value_str(value, 'Scratch', suffix)

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
    def __init__(self):
        self.sgprs = 0
        self.vgprs = 0
        self.code_size = 0
        self.lds = 0
        self.scratch = 0


    def to_string(self, suffixes = True):
        return "{}{}{}{}{}".format(
                get_sgpr_str(self.sgprs, suffixes),
                get_vgpr_str(self.vgprs, suffixes),
                get_code_size_str(self.code_size, suffixes),
                get_lds_str(self.lds, suffixes),
                get_scratch_str(self.scratch, suffixes))


    def __str__(self):
        return self.to_string()

    def add(self, other):
        self.sgprs += other.sgprs
        self.vgprs += other.vgprs
        self.code_size += other.code_size
        self.lds += other.lds
        self.scratch += other.scratch

    def update(self, comp, cmp_fn):
        for name in self.__dict__.keys():
            current = self.__dict__[name]
            if type(current) != tuple:
                current = (0, 0, 0)
            if cmp_fn(current, comp.__dict__[name]):
                self.__dict__[name] = comp.__dict__[name]

    def update_max(self, comp):
        for name in self.__dict__.keys():
            current = self.__dict__[name]
            if type(current) == tuple:
                current = self.__dict__[name][0]
            if comp.__dict__[name][0] > current:
                self.__dict__[name] = comp.__dict__[name]

    def update_min(self, comp):
        for name in self.__dict__.keys():
            current = self.__dict__[name]
            if type(current) == tuple:
                current = self.__dict__[name][0]
            if comp.__dict__[name][0] < current:
                self.__dict__[name] = comp.__dict__[name]

    def update_increase(self, comp):
        for name in self.__dict__.keys():
            if comp.__dict__[name][0] > 0:
                self.__dict__[name] += 1

    def update_decrease(self, comp):
        for name in self.__dict__.keys():
            if comp.__dict__[name][0] < 0:
                self.__dict__[name] += 1

    def is_empty(self):
        return sum(map(lambda x : x[0] if type(x) == tuple else x, self.__dict__.values())) == 0

def get_results(filename):
    file = open(filename, "r")
    lines = file.read().split('\n')

    results = []
    current_stats = si_stats()

    for line in lines:
        re_start = re.compile("^\*\*\* SHADER STATS \*\*\*$")
        re_sgprs = re.compile("^SGPRS: ([0-9]+)$")
        re_vgprs = re.compile("^VGPRS: ([0-9]+)$")
        re_code_size = re.compile("^Code Size: ([0-9]+) bytes$")
        re_lds = re.compile("^LDS: ([0-9]+) blocks$")
        re_scratch = re.compile("^Scratch: ([0-9]+) bytes per wave$")
        re_end = re.compile("^\*+$")

        # First line of stats
        match = re.search(re_start, line)
        if match:
            continue

        match = re.search(re_sgprs, line)
        if match:
            current_stats.sgprs = int(match.groups()[0])
            continue

        match = re.search(re_vgprs, line)
        if match:
            current_stats.vgprs = int(match.groups()[0])
            continue

        match = re.search(re_code_size, line)
        if match:
            current_stats.code_size = int(match.groups()[0])
            continue

        match = re.search(re_lds, line)
        if match:
            current_stats.lds = int(match.groups()[0])
            continue

        match = re.search(re_scratch, line)
        if match:
            current_stats.scratch = int(match.groups()[0])
            continue

        match = re.search(re_end, line)
        if match:
            results.append(current_stats)
            current_stats = si_stats()

    return results


def compare_stats(before, after):
    result = si_stats()
    for name in result.__dict__.keys():
        b = before.__dict__[name]
        a = after.__dict__[name]
        result.__dict__[name] = (a - b, b, a)
    return result

def divide_stats(num, div):
    result = si_stats()
    for name in result.__dict__.keys():
        if div.__dict__[name] == 0:
            result.__dict__[name] = num.__dict__[name]
        else:
            result.__dict__[name] = 100.0 * float(num.__dict__[name]) / float(div.__dict__[name])
    return result

def print_before_after_stats(before, after, divisor = 1):
    result = si_stats()
    for name in result.__dict__.keys():
        b = before.__dict__[name] / divisor
        a = after.__dict__[name] / divisor
        if b == 0:
            percent = format_float(0.0)
        else:
            percent = format_float(100 * float(a - b) / float(b))
        result.__dict__[name] = '{} -> {} ({})'.format(get_str(b,''), get_str(a,''), percent)

    print result

def print_cmp_stats(comp):
    result = si_stats()
    for name in result.__dict__.keys():
        if type(comp.__dict__[name]) != tuple:
            a = 0
            b = 0
        else:
            b = comp.__dict__[name][1]
            a = comp.__dict__[name][2]
        if b == 0:
            percent = format_float(0.0)
        else:
            percent = format_float(100 * float(a - b) / float(b))
        result.__dict__[name] = '{} -> {} ({})'.format(get_str(b,''), get_str(a,''), percent)

    print result


def print_count(stats, divisor):
    result = si_stats()
    for name in result.__dict__.keys():
        count = stats.__dict__[name]
        percent = float(count) / float(divisor)
        result.__dict__[name] = '{} ({})'.format(get_str(count,''), get_str(percent))
    print result.to_string(False)

def compare_results(before_results, after_results):
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
    assert len(before_results) == len(after_results)

    for i in range(0, len(before_results)):
        before = before_results[i]
        after = after_results[i]

        total_before.add(before)
        total_after.add(after)

        comp = compare_stats(before, after)
        if not comp.is_empty():
            num_affected += 1
            total_affected_before.add(before)
            total_affected_after.add(after)
            increases.update_increase(comp)
            decreases.update_decrease(comp)
            max_increase_per.update(comp, cmp_max_per)
            max_decrease_per.update(comp, cmp_min_per)
            max_increase_unit.update(comp, cmp_max_unit)
            max_decrease_unit.update(comp, cmp_min_unit)

    print '{} shaders'.format(len(before_results))
    print "Totals:"
    print_before_after_stats(total_before, total_after)
    print "Totals from affected shaders:"
    print_before_after_stats(total_affected_before, total_affected_after)
    print "Increases:"
    print_count(increases, len(before_results))
    print "Decreases:"
    print_count(decreases, len(after_results))

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


def main():
    before = sys.argv[1]
    after = sys.argv[2]

    compare_results(get_results(before), get_results(after))

if __name__ == "__main__":
    main()
