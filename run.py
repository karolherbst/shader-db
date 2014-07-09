#!/usr/bin/env python3

import re
import sys
import os
import time
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count


def process_directories(items):
    for item in items:
        if os.path.isfile(item):
            yield item
        else:
            for dirpath, _, filenames in os.walk(item):
                for fname in filenames:
                    ext = os.path.splitext(fname)[1]
                    if ext in ['.frag', '.vert', '.shader_test']:
                        yield os.path.join(dirpath, fname)


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

    timebefore = time.time()

    try:
        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate()
        results = (stdout + stderr).decode("utf-8")
    except KeyboardInterrupt:
        exit(1)
    except:
        return filename + " FAIL\n"

    timeafter = time.time()

    with open(filename + '.out', 'w') as file:
        file.write(results)

    current_type = 'UNKNOWN'
    counts = {}
    lines = list(results.split('\n'))

    re_builtin_shader = re.compile(r"shader 0")
    re_fs_8 = re.compile(r"^Native code for .*fragment.*(8-wide|SIMD8)")
    re_fs_16 = re.compile(r"^Native code for .*fragment.*(16-wide|SIMD16)")
    re_gs = re.compile(r"^Native code for .*geometry")
    re_vs = re.compile(r"^Native code for .*vertex")
    re_align = re.compile(r"{ align")
    re_2q = re.compile(r"\(8\).* 2Q };")
    counts["vs  "] = 0
    counts["gs  "] = 0
    counts["fs8 "] = 0
    counts["fs16"] = 0
    for line in lines:
        if (re_builtin_shader.search(line)):
            continue
        elif (re_vs.search(line)):
            current_type = "vs  "
        elif (re_gs.search(line)):
            current_type = "gs  "
        elif (re_fs_8.search(line)):
            current_type = "fs8 "
        elif (re_fs_16.search(line)):
            current_type = "fs16"
        elif (re_align.search(line)):
            # Skip the 2Q (second half) SIMD8 instructions, since the
            # 1Q+2Q pair should be the same cost as a single 1H
            # (SIMD16) instruction, other than icache pressure.
            if current_type != "fs16" or not re_2q.search(line):
                counts[current_type] = counts[current_type] + 1

    timestr = "    {:.3f} secs".format(timeafter - timebefore)
    out = ''
    for k, v in counts.items():
        if v != 0:
            out += "{0:40} {1} : {2:6}{3}\n".format(filename, k, v, timestr)
            timestr = ""
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("shader",
                        nargs='*',
                        default=['shaders'],
                        metavar="<shader_file | shader dir>",
                        help="A shader file or directory containing shader "
                             "files. Defaults to 'shaders/'")
    args = parser.parse_args()

    env_add = {}
    env_add["shader_precompile"] = "true"
    env_add["force_glsl_extensions_warn"] = "true"
    env_add["INTEL_DEBUG"] = "vs,wm,gs"

    os.environ.update(env_add)

    try:
        os.stat("bin/glslparsertest")
    except OSError:
        print("./bin must be a symlink to a built piglit bin directory")
        sys.exit(1)

    runtimebefore = time.time()

    filenames = process_directories(args.shader)

    executor = ThreadPoolExecutor(cpu_count())
    for t in executor.map(run_test, filenames):
        sys.stdout.write(t)

    runtime = time.time() - runtimebefore
    print("shader-db run completed in {:.1f} secs".format(runtime))


if __name__ == "__main__":
    main()
