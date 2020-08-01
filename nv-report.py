#!/usr/bin/python

"""
We're matching lines like

5.shader_test - type: 1, local: 0, shared: 0, gpr: 4, inst: 7, bytes: 56
11.shader_test - type: 1, local: 0, shared: 0, gpr: 4, inst: 1, bytes: 8

although the order of the fields after the dash does not matter, and all
fields, except for the type, are optional.
"""

from __future__ import print_function
import re
import sys

attrs = ("inst", "gpr", "local", "shared", "bytes")

def getgroupvalue(m, groupname):
    if not m[groupname]:
        return 0
    else:
        return int(m[groupname].group(1), 10)

class Stat(object):

    def __init__(self, m=None):
        self.vals = dict.fromkeys(attrs, 0)
        for v in attrs:
            self.vals[v] = getgroupvalue(m, v) if m else 0

    def __eq__(self, other):
        return self.vals == other.vals

class Stats(object):

    def __init__(self):
        self.stats = {}
        self.vals = dict.fromkeys(attrs, 0)

    def record(self, name, stat):
        assert name not in self.stats, name
        self.stats[name] = stat
        for attr in attrs:
            self.vals[attr] += stat.vals[attr]

RE = dict((k, re.compile(regex)) for k, regex in
    [("name", r"^(.*) - ")] +
    [(a, r"%s: (\d+)" % a) for a in ("type",) + attrs]
)

def analyze(fname):
    stats = Stats()
    with open(fname, "r") as f:
        for line in f:
            if line.startswith("Thread "):
                continue
            m = {}
            for attr in ("name", "type") + attrs:
                m[attr] = RE[attr].search(line)
            assert m["name"], line
            assert m["type"], line
            stats.record(m["name"].group(1) + " - " + m["type"].group(1), Stat(m))

    return stats

def diff(a, b):
    percentage = 0.
    if a != 0.:
        percentage = b * 100. / a - 100.
    elif b != 0.:
        percentage = float('inf')
    return "%d -> %d (%.2f%%)" % (a, b, percentage)

def main(argv):
    # Count up each of the metrics in the before and after, and
    # produce hurt/helped comparisons.
    before = analyze(argv[1])
    after = analyze(argv[2])
    keys = set(before.stats.keys()) | set(after.stats.keys())

    helped = Stat()
    hurt = Stat()
    for key in keys:
        if key not in after.stats or key not in before.stats:
            print("Missing", key)
            continue
        a = after.stats[key]
        b = before.stats[key]
        if a != b:
            for attr in attrs:
                aa = a.vals[attr]
                ba = b.vals[attr]
                if aa == ba:
                    continue
                if aa < ba:
                    helped.vals[attr] += 1
                else:
                    hurt.vals[attr] += 1

    for attr in attrs:
        print("total %s in shared programs :" % attr, diff(before.vals[attr], after.vals[attr]))
    print()
    print("%10s " * (len(attrs) + 1) % (("",) + attrs))
    print(("%10s " + "%10d " * len(attrs)) % (("helped",) + tuple(helped.vals[v] for v in attrs)))
    print(("%10s " + "%10d " * len(attrs)) % (("hurt",) + tuple(hurt.vals[v] for v in attrs)))

if __name__ == "__main__":
    main(sys.argv)
