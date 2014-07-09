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

    counts = {}

    lines = (line for line in results.splitlines())
    re_number = re.compile(
        r'Native code for unnamed (fragment|vertex|geometry) shader (?P<number>\d+)')
    for line in lines:
        shader = re_number.match(line)
        if shader and int(shader.group('number')) > 0:
            break
    else:
        raise Exception('Only shader 0 found. {}'.format(filename))

    re_search = re.compile(
        r'(?P<stage>[A-Za-z0-9]+) shader\: (?P<count>\d+) instructions.')
    for line in lines:
        match = re_search.match(line)
        if match is not None:
            counts[match.group('stage')] = int(match.group('count'))

    assert counts, 'File: {} does not have any shaders'.format(filename)

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
