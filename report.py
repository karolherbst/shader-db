#!/usr/bin/env python

import re
import argparse


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
    parser = argparse.ArgumentParser()
    parser.add_argument("before", help="the output of the original code")
    parser.add_argument("after", help="the output of the new code")
    args = parser.parse_args()

    total_before = 0
    total_after = 0
    affected_before = 0
    affected_after = 0

    helped = []
    hurt = []
    lost = []
    gained = []
    for p in args.before:
        (name, type) = p
        namestr = name + " " + type
        before_count = args.before[p]

        if args.after.get(p) != None:
            after_count = args.after[p]

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

    for p in args.after:
        if (args.before.get(p) == None):
            gained.append(p[0] + " " + p[1])

    helped.sort()
    for r in helped:
        print("helped: " + r)
    if len(helped) > 0:
        print("")

    hurt.sort(key=lambda k: float(args.after[k] - args.before[k]) / args.before[k])
    for p in hurt:
        namestr = p[0] + " " + p[1]
        print("HURT:   " + get_result_string(namestr, args.before[p], args.after[p]))
    if len(hurt) > 0:
        print("")

    lost.sort()
    for p in lost:
        print("LOST:   " + p)
    if len(lost) > 0:
        print("")

    gained.sort()
    for p in gained:
        print("GAINED: " + p)
    if len(gained) > 0:
        print("")

    print("total instructions in shared programs: " + change(total_before, total_after))
    print("instructions in affected programs:     " + change(affected_before, affected_after))
    print("GAINED:                                {0}".format(len(gained)))
    print("LOST:                                  {0}".format(len(lost)))


if __name__ == "__main__":
        main()
