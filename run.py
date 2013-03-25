#!/usr/bin/env python3

from getopt import getopt, GetoptError
import re
import sys, os, time
import subprocess
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count

def usage():
    USAGE = """\
Usage: %(progName)s [shader.frag] [shader.vert]

Options:
  -h, --help                Show this message
"""
    print(USAGE % {'progName': sys.argv[0]})
    sys.exit(1)

def run_test(filename):
    if ".out" in filename:
        return ""

    if ".shader_test" in filename:
        command = ['./bin/shader_runner',
                   filename,
                   '-auto',
                   '-fbo']
    else:
        command = ['./bin/glslparsertest',
                   filename,
                   'pass']

    try:
        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    except:
        return filename + " FAIL"

    try:
        (stdout, stderr) = p.communicate()
        results = (stdout + stderr).decode("utf-8")
    except KeyboardInterrupt:
        exit(1)
    except:
        return filename + " FAIL"

    with open(filename + '.out', 'w') as file:
        file.write(results)

    current_type = 'UNKNOWN'
    counts = {}
    lines = list(results.split('\n'))

    re_builtin_shader = re.compile("shader 0")
    re_fs_8 = re.compile("^Native code for fragment.*8-wide")
    re_fs_16 = re.compile("^Native code for fragment.*16-wide")
    re_vs = re.compile("^Native code for vertex")
    re_align = re.compile("{ align")
    counts["ignore"] = 0
    counts["vs  "] = 0
    counts["fs8 "] = 0
    counts["fs16"] = 0
    for line in lines:
        if (re.search(re_builtin_shader, line)):
            current_type = "ignore"
        elif (re.search(re_vs, line)):
            current_type = "vs  "
        elif (re.search(re_fs_8, line)):
            current_type = "fs8 "
        elif (re.search(re_fs_16, line)):
            current_type = "fs16"
        elif (re.search(re_align, line)):
            counts[current_type] = counts[current_type] + 1
    del counts["ignore"]

    out = ''
    for t in counts:
        if counts[t] != 0:
            out += "".join([filename, " ", t, ": ", str(counts[t]), "\n"])
    return out

def main():
    try:
        option_list = [
            "help",
            ]
        options, args = getopt(sys.argv[1:], "h", option_list)
    except GetoptError:
        usage()

    env_add = {}
    env_add["shader_precompile"] = "true"
    env_add["force_glsl_extensions_warn"] = "true"
    env_add["INTEL_DEBUG"] = "vs,wm"

    os.environ.update(env_add)

    for name, value in options:
        if name in ('-h', '--help'):
            usage()

    if len(args) < 1:
        usage()

    try:
        os.stat("bin/glslparsertest")
    except:
        print("./bin must be a symlink to a built piglit bin directory")
        sys.exit(1)

    runtimebefore = time.time()

    executor = ThreadPoolExecutor(cpu_count())
    for t in executor.map(run_test, args):
        sys.stdout.write(t)

    runtimeafter = time.time()
    print("shader-db run completed in {:.1} secs".format(runtimeafter - runtimebefore))

if __name__ == "__main__":
	main()
