#!/usr/bin/python

"""
We're matching lines like

5.shader_test - type: 1, local: 0, gpr: 4, inst: 7, bytes: 56
11.shader_test - type: 1, local: 0, gpr: 4, inst: 1, bytes: 8
"""

import re
import sys

class Stat(object):

    def __init__(self, m=None):
        if m:
            self.local = int(m.group("local"), 10)
            self.gpr = int(m.group("gpr"), 10)
            self.inst = int(m.group("inst"), 10)
            self.bytes = int(m.group("bytes"), 10)
        else:
            self.local = 0
            self.gpr = 0
            self.inst = 0
            self.bytes = 0

    def __eq__(self, other):
        return (self.local == other.local and
                self.gpr == other.gpr and
                self.inst == other.inst and
                self.bytes == other.bytes)

class Stats(object):

    def __init__(self):
        self.stats = {}
        self.local = 0
        self.gpr = 0
        self.inst = 0
        self.bytes = 0

    def record(self, name, stat):
        assert name not in self.stats, name
        self.stats[name] = stat
        for attr in ("local", "gpr", "inst", "bytes"):
            setattr(self, attr, getattr(self, attr) + getattr(stat, attr))

RE = re.compile(r"^(?P<name>.*) - type: (?P<type>\d+), local: (?P<local>\d+), "
                r"gpr: (?P<gpr>\d+), inst: (?P<inst>\d+), "
                r"bytes: (?P<bytes>\d+)$")

def analyze(fname):
    stats = Stats()
    with open(fname, "r") as f:
        for line in f.xreadlines():
            if line.startswith("Thread "):
                continue
            m = RE.match(line)
            assert m, line
            stats.record(m.group("name") + " - " + m.group("type"), Stat(m))

    return stats

def diff(a, b):
    return "%d -> %d (%.2f%%)" % (a, b, b * 100. / a - 100.)

def main(argv):
    # Count up each of the metrics in the before and after, and
    # produce hurt/helped comparisons.
    before = analyze(argv[1])
    after = analyze(argv[2])
    keys = before.stats.keys()
    assert after.stats.keys() == keys

    helped = Stat()
    hurt = Stat()
    for key in keys:
        a = after.stats[key]
        b = before.stats[key]
        if a != b:
            for attr in ("local", "gpr", "inst", "bytes"):
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
    print "total local used in shared programs   :", diff(before.local, after.local)
    print
    print "%10s %10s %10s %10s %10s " % ("", "local", "gpr", "inst", "bytes")
    print "%10s " % "helped",
    for attr in ("local", "gpr", "inst", "bytes"):
        print "%10d " % getattr(helped, attr),
    print
    print "%10s " % "hurt",
    for attr in ("local", "gpr", "inst", "bytes"):
        print "%10d " % getattr(hurt, attr),


if __name__ == "__main__":
    main(sys.argv)
