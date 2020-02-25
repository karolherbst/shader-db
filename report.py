#!/usr/bin/env python3

import re
import argparse
import math
import statistics
from scipy import stats
import numpy as np


def get_results(filename, args):
    file = open(filename, "r")
    lines = file.read().split('\n')

    results = {}
    results["time"] = 0

    time_match = re.compile(r"Thread \S+ took (\S+) seconds")
    re_match = re.compile(r"(\S+) - (.*) shader: (.*)")
    for line in lines:
        match = re.search(time_match, line)
        if match is not None:
            results["time"] = results["time"] + float(match.group(1))
            continue

        match = re.search(re_match, line)
        if match is None:
            continue

        groups = match.groups()

        app = groups[0]
        stage = groups[1]
        stats = groups[2]

        if args.stage and args.stage != stage:
            continue

        result_group = {}
        for stat in stats.split(', '):
            stat_split_spaces = stat.split(' ')
            name = stat_split_spaces[1]
            val = stat_split_spaces[0]
            # Skipping "Promoted 0 constants" and "compacted..." on i965.
            # We should probably change "compacted" to just a shader size
            # in bytes.
            if len(stat_split_spaces) != 2 :
                continue

            if name == "inst":
                name = "instructions"

            if name == "spills:fills":
                (spills, fills) = val.split(':')
                result_group['spills'] = int(spills)
                result_group['fills'] = int(fills)
            elif val.isnumeric():
                result_group[name] = int(val)

        results[(app, stage)] = result_group
    return results


def format_percent(frac):
    """Converts a factional value (typically 0.0 to 1.0) to a string as a percentage"""
    if abs(frac) > 0.0 and abs(frac) < 0.0001:
        return "<.01%"
    else:
        return "{:.2f}%".format(frac * 100)

def format_num(n):
    assert n >= 0
    if n - math.floor(n) < 0.01:
        return str(math.floor(n))
    else:
        return "{:.2f}".format(n)

def get_delta(b, a):
    if b != 0 and a != 0:
        frac = float(a) / float(b) - 1.0
        return ' ({})'.format(format_percent(frac))
    else:
        return ''


def change(b, a):
    return format_num(b) + " -> " + format_num(a) + get_delta(b, a)


def get_result_string(p, b, a):
    p = p + ": "
    while len(p) < 50:
        p = p + ' '
    return p + change(b, a)

def get_spill_fill_if_change(m, b, a):
    if m in ("spills", "fills"):
        return ''

    if b["spills"] == a["spills"] and b["fills"] == a["fills"]:
        return ''

    return " (spills: " + change(b["spills"], a["spills"]) + "; fills: " + change(b["fills"], a["fills"]) + ")"

def split_list(string):
    return string.split(",")


def gather_statistics(changes, before, after, m):
    stats = (0.0, 0, 0.0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

    if changes:
        absolute = [abs(before[p][m] - after[p][m]) for p in changes]
        relative = [0 if before[p][m] == 0 else abs(before[p][m] - after[p][m]) / before[p][m] for p in changes]

        stats = (statistics.mean(absolute),
                 statistics.median(absolute),
                 min(absolute),
                 max(absolute),
                 statistics.mean(relative),
                 statistics.median(relative),
                 min(relative),
                 max(relative))

    return stats


def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), stats.sem(a)
    h = se * stats.t.ppf((1 + confidence) / 2., n - 1)
    return m, m - h, m + h


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurements", "-m", type=split_list,
                        help="comma-separated list of measurements to report")
    parser.add_argument("--summary-only", "-s", action="store_true", default=False,
                        help="do not show the per-shader helped / hurt data")
    parser.add_argument("--changes-only", "-c", action="store_true", default=False,
                        help="only show measurements that have changes")
    parser.add_argument("--stage", "-S", help="limit results to specified shader stage")
    parser.add_argument("--ignore-loops", action="store_true", help="ignore loops", default=False)
    parser.add_argument("before", help="the output of the original code")
    parser.add_argument("after", help="the output of the new code")
    args = parser.parse_args()

    before = get_results(args.before, args)
    after = get_results(args.after, args)

    # Grab these and remove them from the dictionary
    time_before = before.pop("time")
    time_after = after.pop("time")

    total_before = {}
    total_after = {}
    affected_before = {}
    affected_after = {}
    num_hurt = {}
    num_helped = {}
    helped_statistics = {}
    hurt_statistics = {}
    confidence_interval = {}

    # If no set of measurements is specified, pick an arbitrary shader and use
    # the ones it has.  The assumption is that all shaders will have had the
    # same set of measurements printed
    if not args.measurements:
        args.measurements = []

        for p in before:
            for m in before[p]:
                args.measurements.append(m)
            break

    for m in args.measurements:

        if m == "inst":
            m = "instructions"

        total_before[m] = 0
        total_after[m] = 0
        affected_before[m] = 0
        affected_after[m] = 0

        helped = []
        hurt = []
        for p in before:
            before_count = before[p][m]

            if after.get(p) is None:
                continue

            # If the number of loops changed, then we may have unrolled some
            # loops, in which case other measurements will be misleading.
            if m != "loops" and before[p]["loops"] != after[p]["loops"] and not args.ignore_loops:
                continue

            after_count = after[p][m]

            total_before[m] += before_count
            total_after[m] += after_count

            if before_count != after_count:
                affected_before[m] += before_count
                affected_after[m] += after_count

                higher_is_better = m == "threads"

                if (after_count > before_count) ^ higher_is_better:
                    hurt.append(p)
                else:
                    helped.append(p)

        if not args.summary_only:
            helped.sort(
                key=lambda k: after[k][m] if before[k][m] == 0 else float(before[k][m] - after[k][m]) / before[k][m])
            for p in helped:
                namestr = p[0] + " " + p[1]
                print(m + " helped:   " +
                      get_result_string(namestr, before[p][m], after[p][m]) +
                      get_spill_fill_if_change(m, before[p], after[p]))
            if helped:
                print("")

            hurt.sort(
                key=lambda k: after[k][m] if before[k][m] == 0 else float(after[k][m] - before[k][m]) / before[k][m])
            for p in hurt:
                namestr = p[0] + " " + p[1]
                print(m + " HURT:   " +
                      get_result_string(namestr, before[p][m], after[p][m]) +
                      get_spill_fill_if_change(m, before[p], after[p]))
            if hurt:
                print("")

        helped_statistics[m] = gather_statistics(helped, before, after, m)
        hurt_statistics[m] = gather_statistics(hurt, before, after, m)

        num_helped[m] = len(helped)
        num_hurt[m] = len(hurt)

        # Statistics for spills and fills is usually meaningless.
        if m in ["spills", "fills"]:
            continue

        if num_hurt[m] + num_helped[m] > 3:
            A = [after[p][m] - before[p][m] for p in helped + hurt]
            B = [0 if before[p][m] == 0 else (after[p][m] - before[p][m]) / before[p][m] for p in helped + hurt]

            confidence_interval[m] = (mean_confidence_interval(A), mean_confidence_interval(B))

    lost = []
    gained = []

    for p in before:
        if after.get(p) is None:
            lost.append(p[0] + " " + p[1])

    for p in after:
        if before.get(p) is None:
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

        if m == "inst":
            m = "instructions"

        if num_helped[m] > 0 or num_hurt[m] > 0:
            any_helped_or_hurt = True

        if num_helped[m] > 0 or num_hurt[m] > 0 or not args.changes_only:
            print("total {0} in shared programs: {1}\n"
                  "{0} in affected programs: {2}\n"
                  "helped: {3}\n"
                  "HURT: {4}".format(
                      m,
                      change(total_before[m], total_after[m]),
                      change(affected_before[m], affected_after[m]),
                      num_helped[m],
                      num_hurt[m]))

            # Statistics for spills and fills is usually meaningless.
            if m in ["spills", "fills"]:
                print()
                continue

            if num_helped[m] > 2 or (num_helped[m] > 0 and num_hurt[m] > 0):
                (avg_abs, med_abs, lo_abs, hi_abs, avg_rel, med_rel, lo_rel, hi_rel) = helped_statistics[m]

                print("helped stats (abs) min: {} max: {} x\u0304: {:.2f} x\u0303: {}".format(
                    lo_abs, hi_abs, avg_abs, int(med_abs)))
                print("helped stats (rel) min: {} max: {} x\u0304: {} x\u0303: {}".format(
                    format_percent(lo_rel),
                    format_percent(hi_rel),
                    format_percent(avg_rel),
                    format_percent(med_rel)))

            if num_hurt[m] > 2 or (num_hurt[m] > 0 and num_helped[m] > 0):
                (avg_abs, med_abs, lo_abs, hi_abs, avg_rel, med_rel, lo_rel, hi_rel) = hurt_statistics[m]

                print("HURT stats (abs)   min: {} max: {} x\u0304: {:.2f} x\u0303: {}".format(
                    lo_abs, hi_abs, avg_abs, int(med_abs)))
                print("HURT stats (rel)   min: {} max: {} x\u0304: {} x\u0303: {}".format(
                    format_percent(lo_rel),
                    format_percent(hi_rel),
                    format_percent(avg_rel),
                    format_percent(med_rel)))

            if m in confidence_interval:
                print("95% mean confidence interval for {} value: {:.2f} {:.2f}".format(m,
                                                                                        confidence_interval[m][0][1],
                                                                                        confidence_interval[m][0][2]))
                print("95% mean confidence interval for {} %-change: {} {}".format(m,
                                                                                   format_percent(confidence_interval[m][1][1]),
                                                                                   format_percent(confidence_interval[m][1][2])))

                # Be very, very conservative about applying results
                # based on the confidence intervals.  Neither interval
                # can include zero, and both intervals must be on the
                # same side of zero.
                if confidence_interval[m][0][1] < 0 and confidence_interval[m][0][2] > 0:
                    print("Inconclusive result (value mean confidence interval includes 0).")
                elif confidence_interval[m][1][1] < 0 and confidence_interval[m][1][2] > 0:
                    print("Inconclusive result (%-change mean confidence interval includes 0).")
                elif (confidence_interval[m][0][1] < 0) != (confidence_interval[m][1][1] < 0):
                    print("Inconclusive result (value mean confidence interval and %-change mean confidence interval disagree).")
                elif confidence_interval[m][0][1] < 0:
                    print("{} are helped.".format(m.capitalize()))
                else:
                    print("{} are HURT.".format(m.capitalize()))

            print()


    if lost or gained or not args.changes_only:
        print("LOST:   " + str(len(lost)))
        print("GAINED: " + str(len(gained)))
    else:
        if not any_helped_or_hurt:
            print("No changes.")

    print("")
    print("Total CPU time (seconds): " + change(time_before, time_after))

if __name__ == "__main__":
    main()
