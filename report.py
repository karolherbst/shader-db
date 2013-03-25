#!/usr/bin/env python

from getopt import getopt, GetoptError
import re
import sys, os
import subprocess

def usage():
    USAGE = """\
Usage: %(progName)s <before> <after>

Options:
  -h, --help                Show this message
"""
    print USAGE % {'progName': sys.argv[0]}
    sys.exit(1)

def get_results(filename):
    file = open(filename, "r")
    lines = file.read().split('\n')

    results = {}

    re_match = re.compile("(\S*)\s*(\S*)\s*:\s*(\S*)")
    for line in lines:
        match = re.search(re_match, line)
        if match == None:
            continue

        groups = match.groups()
        print(groups)
        count = int(groups[2])
        if count != 0:
            results[(groups[0], groups[1])] = count

    return results

def get_delta(b, a):
    if b != 0 and a != 0:
        frac = float(a) / float(b) - 1.0
        return ' ({:.2f}%)'.format(frac * 100.0)
    else:
        return ''

def change(b, a):
    return str(b) + " -> " + str(a) + get_delta(b, a)

def get_result_string(p, b, a):
    p = p + ": "
    while len(p) < 50:
        p = p + ' '
    return p + change(b, a)

def main():
    try:
        option_list = [
            "help",
            ]
        options, args = getopt(sys.argv[1:], "h", option_list)
    except GetoptError:
        usage()

    for name, value in options:
        if name in ('-h', '--help'):
            usage()

    if len(args) != 2:
        usage()

    before = get_results(args[0])
    after = get_results(args[1])

    total_before = 0
    total_after = 0
    affected_before = 0
    affected_after = 0

    helped = []
    hurt = []
    lost = []
    gained = []
    for p in before:
        (name, type) = p
        namestr = name + " " + type
        before_count = before[p]

        if after.get(p) != None:
            after_count = after[p]

            total_before += before_count
            total_after += after_count

            if before_count != after_count:
                affected_before += before_count
                affected_after += after_count

                result = get_result_string(namestr, before_count, after_count)
                if after_count > before_count:
                    hurt.append(p)
                else:
                    helped.append(result)
        else:
            lost.append(namestr)

    for p in after:
        if (before.get(p) == None):
            gained.append(p[0] + " " + p[1])

    helped.sort()
    for r in helped:
        print "helped: " + r
    if len(helped) > 0:
        print ""

    def hurt_sort(k1, k2):
        if (float(after[k1] - before[k1]) / before[k1] >
            float(after[k2] - before[k2]) / before[k2]):
            return 1
        else:
            return -1

    hurt.sort(cmp=hurt_sort)
    for p in hurt:
        namestr = p[0] + " " + p[1]
        print "HURT:   " + get_result_string(namestr, before[p], after[p])
    if len(hurt) > 0:
        print ""

    lost.sort()
    for p in lost:
        print "LOST:   " + p
    if len(lost) > 0:
        print ""

    gained.sort()
    for p in gained:
        print "GAINED: " + p
    if len(gained) > 0:
        print ""

    print "total instructions in shared programs: " + change(total_before, total_after)
    print "instructions in affected programs:     " + change(affected_before, affected_after)

if __name__ == "__main__":
	main()
