#!/usr/bin/env python

from getopt import getopt, GetoptError
import re
import sys, os
import subprocess

def usage():
    USAGE = """\
Usage: %(progName)s [shader.frag] [shader.vert]

Options:
  -h, --help                Show this message
"""
    print USAGE % {'progName': sys.argv[0]}
    sys.exit(1)

def run_test(filename):
    command = ['/home/anholt/src/piglit/bin/glslparsertest',
               filename,
               'pass']

    env_add = {}
    env_add["shader_precompile"] = "true"
    env_add["INTEL_DEBUG"] = "vs,wm"

    env = os.environ.copy()
    env.update(env_add)

    try:
        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env)
    except:
        print filename + " FAIL"
        return

    try:
        (stdout, stderr) = p.communicate()
        results = stdout + stderr
    except KeyboardInterrupt:
        exit(1)
    except:
        print filename + " FAIL "
        return

    with open(filename + '.out', 'w') as file:
        file.write(results)

    current_type = 'UNKNOWN'
    counts = {}
    lines = list(results.split('\n'))

    re_fs_8 = re.compile("^Native code for fragment.*8-wide")
    re_fs_16 = re.compile("^Native code for fragment.*16-wide")
    re_vs = re.compile("^Native code for vertex")
    re_align = re.compile("{ align")
    counts["vs  "] = 0
    counts["fs8 "] = 0
    counts["fs16"] = 0
    for line in lines:
        if (re.search(re_vs, line)):
            current_type = "vs  "
        elif (re.search(re_fs_8, line)):
            current_type = "fs8 "
        elif (re.search(re_fs_16, line)):
            current_type = "fs16"
        elif (re.search(re_align, line)):
            counts[current_type] = counts[current_type] + 1

    for t in counts:
        if counts[t] != 0:
            print filename + " " + t + ": " + str(counts[t])
            sys.stdout.flush()

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

    if len(args) < 1:
        usage()

    for filename in args:
        run_test(filename)

if __name__ == "__main__":
	main()
