#!/usr/bin/env python

import re
import argparse


def get_results(filename):
    file = open(filename, "r")
    lines = file.read().split('\n')

    results = {}

    re_match = re.compile(r"(\S+) - (.S \S+) shader: (\S*) inst, (\S*) loops")
    for line in lines:
        match = re.search(re_match, line)
        if match is None:
            continue

        groups = match.groups()
        count = int(groups[2])
        loop = int(groups[3])
        if count != 0:
            results[(groups[0], groups[1])] = count, loop

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
    parser.add_argument("before", type=get_results, help="the output of the original code")
    parser.add_argument("after", type=get_results, help="the output of the new code")
    args = parser.parse_args()

    total_before = 0
    total_after = 0
    total_before_loop = 0
    total_after_loop = 0
    affected_before = 0
    affected_after = 0

    helped = []
    hurt = []
    lost = []
    gained = []
    loop_change = []
    for p in args.before:
        (name, type) = p
        namestr = name + " " + type
        before_count = args.before[p][0]
        before_loop = args.before[p][1]

        if args.after.get(p) is not None:
            after_count = args.after[p][0]
            after_loop = args.after[p][1]

            total_before_loop += before_loop
            total_after_loop += after_loop

            if before_loop == after_loop:
                total_before += before_count
                total_after += after_count

            if before_count != after_count:
                affected_before += before_count
                affected_after += after_count

                if after_loop != before_loop:
                    loop_change.append(p);
                elif after_count > before_count:
                    hurt.append(p)
                else:
                    helped.append(p)
        else:
            lost.append(namestr)

    for p in args.after:
        if args.before.get(p) is None:
            gained.append(p[0] + " " + p[1])

    helped.sort(
        key=lambda k: float(args.before[k][0] - args.after[k][0]) / args.before[k][0])
    for p in helped:
        namestr = p[0] + " " + p[1]
        print("helped:   " + get_result_string(
            namestr, args.before[p][0], args.after[p][0]))
    if len(helped) > 0:
        print("")

    hurt.sort(
        key=lambda k: float(args.after[k][0] - args.before[k][0]) / args.before[k][0])
    for p in hurt:
        namestr = p[0] + " " + p[1]
        print("HURT:   " + get_result_string(
            namestr, args.before[p][0], args.after[p][0]))
    if len(hurt) > 0:
        print("")

    for p in loop_change:
        namestr = p[0] + " " + p[1]
        print("LOOP CHANGE (" + str(args.before[p][1]) + " -> " + str(args.after[p][1]) +
        "): " + get_result_string(namestr, args.before[p][0], args.after[p][0]))
    if len(loop_change) > 0:
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

    print("total instructions in shared programs: {}\n"
          "instructions in affected programs:     {}\n"
          "total loops in shared programs:        {}\n"
          "helped:                                {}\n"
          "HURT:                                  {}\n"
          "GAINED:                                {}\n"
          "LOST:                                  {}".format(
              change(total_before, total_after),
              change(affected_before, affected_after),
              change(total_before_loop, total_after_loop),
              len(helped),
              len(hurt),
              len(gained),
              len(lost)))


if __name__ == "__main__":
    main()
