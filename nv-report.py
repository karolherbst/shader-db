#!/usr/bin/python

"""
We're matching lines like

5.shader_test - type: 1, local: 0, shared: 0, gpr: 4, inst: 7, bytes: 56
11.shader_test - type: 1, local: 0, shared: 0, gpr: 4, inst: 1, bytes: 8

although the order of the fields after the dash does not matter, and all
fields, except for the type, are optional.
"""

import re
import sys


def getgroupvalue(m, groupname):
    if not m[groupname]:
        return 0
    else:
        return int(m[groupname].group(1), 10)

class Stat(object):

    def __init__(self, m=None):
        if m:
            self.local = getgroupvalue(m, "local")
            self.shared = getgroupvalue(m, "shared")
            self.gpr = getgroupvalue(m, "gpr")
            self.inst = getgroupvalue(m, "inst")
            self.bytes = getgroupvalue(m, "bytes")
        else:
            self.local = 0
            self.shared = 0
            self.gpr = 0
            self.inst = 0
            self.bytes = 0

    def __eq__(self, other):
        return (self.local == other.local and
                self.shared == other.shared and
                self.gpr == other.gpr and
                self.inst == other.inst and
                self.bytes == other.bytes)

class Stats(object):

    def __init__(self):
        self.stats = {}
        self.local = 0
        self.shared = 0
        self.gpr = 0
        self.inst = 0
        self.bytes = 0

    def record(self, name, stat):
        assert name not in self.stats, name
        self.stats[name] = stat
        for attr in ("local", "shared", "gpr", "inst", "bytes"):
            setattr(self, attr, getattr(self, attr) + getattr(stat, attr))

RE = {
        "name":   re.compile(r"^(.*) - "),
        "type":   re.compile(r"type: (\d+)"),
        "local":  re.compile(r"local: (\d+)"),
        "shared": re.compile(r"shared: (\d+)"),
        "gpr":    re.compile(r"gpr: (\d+)"),
        "inst":   re.compile(r"inst: (\d+)"),
        "bytes":  re.compile(r"bytes: (\d+)")
}

def analyze(fname):
    stats = Stats()
    with open(fname, "r") as f:
        for line in f.xreadlines():
            if line.startswith("Thread "):
                continue
            m = {}
            for attr in ("name", "type", "local", "shared", "gpr", "inst", "bytes"):
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
    keys = before.stats.keys()
    assert set(after.stats.keys()) == set(keys)

    helped = Stat()
    hurt = Stat()
    for key in keys:
        a = after.stats[key]
        b = before.stats[key]
        if a != b:
            for attr in ("local", "shared", "gpr", "inst", "bytes"):
                aa = getattr(a, attr)
                ba = getattr(b, attr)
                if aa == ba:
                    continue
                if aa < ba:
                    setattr(helped, attr,
                            getattr(helped, attr) + 1)
                else:
                    setattr(hurt, attr,
                            getattr(hurt, attr) + 1)

    print "total instructions in shared programs :", diff(before.inst, after.inst)
    print "total gprs used in shared programs    :", diff(before.gpr, after.gpr)
    print "total shared used in shared programs  :", diff(before.shared, after.shared)
    print "total local used in shared programs   :", diff(before.local, after.local)
    print
    print "%10s %10s %10s %10s %10s %10s " % ("", "local", "shared", "gpr", "inst", "bytes")
    print "%10s " % "helped",
    for attr in ("local", "shared", "gpr", "inst", "bytes"):
        print "%10d " % getattr(helped, attr),
    print
    print "%10s " % "hurt",
    for attr in ("local", "shared", "gpr", "inst", "bytes"):
        print "%10d " % getattr(hurt, attr),


if __name__ == "__main__":
    main(sys.argv)
