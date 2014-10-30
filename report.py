#!/usr/bin/env python

import re
import argparse


def get_results(filename):
    file = open(filename, "r")
    lines = file.read().split('\n')

    results = {}

    re_match = re.compile(r"(\S*)\s*(\S*)\s*:\s*(\S*)\s*(\S*)")
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
    total_loop_before = 0;
    total_loop_after = 0;
    affected_before = 0
    affected_after = 0

    helped = []
    hurt = []
    unchanged = []
    lost = []
    gained = []
    for p in args.before:
        (name, type) = p
        namestr = name + " " + type
        before_count = args.before[p][0]
        before_loop_count = args.before[p][1]

        if args.after.get(p) is not None:
            after_count = args.after[p][0]
            after_loop_count = args.after[p][1]

            total_before += before_count
            total_loop_before += before_loop_count
            total_after += after_count
            total_loop_after += after_loop_count

            if before_count != after_count:
                affected_before += before_count
                affected_after += after_count

            result = get_result_string(namestr, before_count, after_count)
            if after_count > before_count and after_loop_count >= before_loop_count:
                hurt.append(p)
            elif after_count == before_count:
                unchanged.append(result)
            else:
                res = (result, before_loop_count, after_loop_count)
                helped.append(res)
        else:
            lost.append(namestr)

    for p in args.after:
        if args.before.get(p) is None:
            gained.append(p[0] + " " + p[1])

    helped.sort()
    for r in helped:
        if (r[1] > r[2]):
            print("helped: " + r[0] + " loop: " + change(r[1], r[2]))
        else:
            print("helped: " + r[0])
    if len(helped) > 0:
        print("")

    unchanged.sort()
    for r in unchanged:
        print("unchanged: " + r)
    if len(unchanged) > 0:
        print("")

    hurt.sort(
        key=lambda k: float(args.after[k][0] - args.before[k][0]) / args.before[k][0])
    for p in hurt:
        namestr = p[0] + " " + p[1]
        print("HURT:   " + get_result_string(
            namestr, args.before[p][0], args.after[p][0]) +
              "  loop: " + change(args.before[p][1], args.after[p][1]))
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

    print("total instructions in shared programs: {0}\n"
          "instructions in affected programs:     {1}\n"
          "total loops in shared programs:        {2}\n"
          "GAINED:                                {3}\n"
          "LOST:                                  {4}".format(
              change(total_before, total_after),
              change(affected_before, affected_after),
              change(total_loop_before, total_loop_after),
              len(gained),
              len(lost)))


if __name__ == "__main__":
    main()
