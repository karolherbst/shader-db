#!/usr/bin/env python3

import re
import argparse


def get_results(filename):
    file = open(filename, "r")
    lines = file.read().split('\n')

    results = {}

    re_match = re.compile(r"(\S+) - (\S+ \S+) shader: (\S*) inst, (\S*) loops, (\S*) cycles, (\S*):(\S*) spills:fills")
    for line in lines:
        match = re.search(re_match, line)
        if match is None:
            continue

        groups = match.groups()
        inst_count = int(groups[2])
        loop_count = int(groups[3])
        cycle_count = int(groups[4])
        spill_count = int(groups[5])
        fill_count = int(groups[6])
        if inst_count != 0:
            results[(groups[0], groups[1])] = {
                "instructions": inst_count,
                "spills": spill_count,
                "fills": fill_count,
                "cycles": cycle_count,
                "loops": loop_count
            }

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

def split_list(string):
    return string.split(",")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurements", "-m", type=split_list,
                        default=["instructions", "cycles", "loops", "spills", "fills"],
                        help="comma-separated list of measurements to report")
    parser.add_argument("--summary-only", "-s", action="store_true", default=False,
                        help="do not show the per-shader helped / hurt data")
    parser.add_argument("--changes-only", "-c", action="store_true", default=False,
                        help="only show measurements that have changes")
    parser.add_argument("before", type=get_results, help="the output of the original code")
    parser.add_argument("after", type=get_results, help="the output of the new code")
    args = parser.parse_args()

    total_before = {}
    total_after = {}
    affected_before = {}
    affected_after = {}
    num_hurt = {}
    num_helped = {}

    for m in args.measurements:
        total_before[m] = 0
        total_after[m] = 0
        affected_before[m] = 0
        affected_after[m] = 0

        helped = []
        hurt = []
        for p in args.before:
            before_count = args.before[p][m]

            if args.after.get(p) is None:
                continue

            # If the number of loops changed, then we may have unrolled some
            # loops, in which case other measurements will be misleading.
            if m != "loops" and args.before[p]["loops"] != args.after[p]["loops"]:
                continue

            after_count = args.after[p][m]

            total_before[m] += before_count
            total_after[m] += after_count

            if before_count != after_count:
                affected_before[m] += before_count
                affected_after[m] += after_count

                if after_count > before_count:
                    hurt.append(p)
                else:
                    helped.append(p)

        if not args.summary_only:
            helped.sort(
                key=lambda k: args.after[k][m] if args.before[k][m] == 0 else float(args.before[k][m] - args.after[k][m]) / args.before[k][m])
            for p in helped:
                namestr = p[0] + " " + p[1]
                print(m + " helped:   " + get_result_string(
                    namestr, args.before[p][m], args.after[p][m]))
            if helped:
                print("")

            hurt.sort(
                key=lambda k: args.after[k][m] if args.before[k][m] == 0 else float(args.after[k][m] - args.before[k][m]) / args.before[k][m])
            for p in hurt:
                namestr = p[0] + " " + p[1]
                print(m + " HURT:   " + get_result_string(
                    namestr, args.before[p][m], args.after[p][m]))
            if hurt:
                print("")

        num_helped[m] = len(helped)
        num_hurt[m] = len(hurt)


    lost = []
    gained = []

    for p in args.before:
        if args.after.get(p) is None:
            lost.append(p[0] + " " + p[1])

    for p in args.after:
        if args.before.get(p) is None:
            gained.append(p[0] + " " + p[1])

    if not args.summary_only:
        lost.sort()
        for p in lost:
            print("LOST:   " + p)
        if lost:
            print("")

        gained.sort()
        for p in gained:
            print("GAINED: " + p)
        if gained:
            print("")

    any_helped_or_hurt = False
    for m in args.measurements:
        if num_helped[m] > 0 or num_hurt[m] > 0:
            any_helped_or_hurt = True

        if num_helped[m] > 0 or num_hurt[m] > 0 or not args.changes_only:
            print("total {0} in shared programs: {1}\n"
                  "{0} in affected programs: {2}\n"
                  "helped: {3}\n"
                  "HURT: {4}\n".format(
	              m,
	              change(total_before[m], total_after[m]),
	              change(affected_before[m], affected_after[m]),
	              num_helped[m],
	              num_hurt[m]))


    if lost or gained or not args.changes_only:
        print("LOST:   " + str(len(lost)))
        print("GAINED: " + str(len(gained)))
    else:
        if not any_helped_or_hurt:
            print("No changes.")

if __name__ == "__main__":
    main()
