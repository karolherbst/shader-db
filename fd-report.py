#!/usr/bin/python

"""
We're matching groups of lines like

SHADER-DB: FRAG prog 22/1: 16 instructions, 32 dwords
SHADER-DB: FRAG prog 22/1: 0 half, 6 full
SHADER-DB: FRAG prog 22/1: 0 const, 0 constlen
"""

import re
import sys

class Stat(object):

    def __init__(self, m=None):
        if m:
            self.half = int(m.group("half"), 10)
            self.full = int(m.group("full"), 10)
            self.const = int(m.group("const"), 10)
            self.instr = int(m.group("instr"), 10)
            self.dwords = int(m.group("dwords"), 10)
        else:
            self.half = 0
            self.full = 0
            self.const = 0
            self.instr = 0
            self.dwords = 0

    def __eq__(self, other):
        return (self.half == other.half and
                self.full == other.full and
                self.const == other.const and
                self.instr == other.instr and
                self.dwords == other.dwords)

class Stats(object):

    def __init__(self):
        self.stats = {}
        self.half = 0
        self.full = 0
        self.const = 0
        self.instr = 0
        self.dwords = 0

    def record(self, name, stat):
        assert name not in self.stats, name
        self.stats[name] = stat
        for attr in ("half", "full", "const", "instr", "dwords"):
            setattr(self, attr, getattr(self, attr) + getattr(stat, attr))

#RE = re.compile(r"^(?P<name>.*) - type: (?P<type>\d+), local: (?P<local>\d+), "
#                r"gpr: (?P<gpr>\d+), inst: (?P<inst>\d+), "
#                r"bytes: (?P<bytes>\d+)$")
#SHADER-DB: FRAG prog 22/1: 16 instructions, 32 dwords
#SHADER-DB: FRAG prog 22/1: 0 half, 6 full
#SHADER-DB: FRAG prog 22/1: 0 const, 0 constlen
RE1 = re.compile(r"^SHADER-DB: (?P<name>[A-Z]+ prog \d+/\d+): (?P<line>.*)$")
RE2 = re.compile(r"^(?P<instr>\d+) instructions, (?P<dwords>\d+) dwords, (?P<half>\d+) half, (?P<full>\d+) full, (?P<const>\d+) const, \d+ constlen$")

def analyze(fname):
    stats = Stats()
    with open(fname, "r") as f:
        i = 0
        str = None
        for line in f.xreadlines():
            m1 = RE1.match(line)
            if m1:
                l = m1.group("line")
                if str:
                    str = str + ", " + l
                else:
                    str = l
                i = i + 1
                if i == 3:
                    #print(m1.group("name") + ": " + str)
                    m2 = RE2.match(str)
                    assert m2, str
                    stats.record(m1.group("name"), Stat(m2))
                    i = 0
                    str = None

    return stats

def diff(a, b):
    if a == 0:
        return "%d -> %d" % (a, b)
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
        if not key in after.stats and key in before.stats:
            continue
        a = after.stats[key]
        b = before.stats[key]
        if a != b:
            for attr in ("half", "full", "const", "instr", "dwords"):
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

    print "total instructions in shared programs:         ", diff(before.instr, after.instr)
    print "total dwords in shared programs:               ", diff(before.dwords, after.dwords)
    print "total full registers used in shared programs:  ", diff(before.full, after.full)
    print "total half registers used in shader programs:  ", diff(before.half, after.half)
    print "total const registers used in shared programs: ", diff(before.const, after.const)
    print
    print "%10s %10s %10s %10s %10s %10s" % ("", "half", "full", "const", "instr", "dwords")
    print "%10s " % "helped",
    for attr in ("half", "full", "const", "instr", "dwords"):
        print "%10d " % getattr(helped, attr),
    print
    print "%10s " % "hurt",
    for attr in ("half", "full", "const", "instr", "dwords"):
        print "%10d " % getattr(hurt, attr),


if __name__ == "__main__":
    main(sys.argv)
