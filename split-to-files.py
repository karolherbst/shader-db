#!/usr/bin/env python3

import re
import os
import argparse


def parse_input(infile):
    shaders = dict()
    shadertuple = ("bad", 0)
    prognum = ""
    reading = False

    for line in infile.splitlines():
        declmatch = re.match(
            r"GLSL (.*) shader (.*) source for linked program (.*):", line)
        if declmatch:
            shadertype = declmatch.group(1)
            shadernum = declmatch.group(2)
            prognum = declmatch.group(3)
            shadertuple = (shadertype, shadernum)

            # don't save driver-internal shaders.
            if prognum == "0":
                continue

            if prognum not in shaders:
                shaders[prognum] = dict()
            if shadertuple in shaders[prognum]:
                print("Warning: duplicate", shadertype, " shader ", shadernum,
                      "in program", prognum, "...tossing old shader.")
            shaders[prognum][shadertuple] = ''
            reading = True
            print("Reading program {0} {1} shader {2}".format(
                prognum, shadertype, shadernum))
        elif re.match(r"GLSL IR for ", line):
            reading = False
        elif re.match(r"GLSL source for ", line):
            reading = False
        elif reading:
            shaders[prognum][shadertuple] += line + '\n'

    return shaders


def write_shader_test(filename, shaders):
    print("Writing {0}".format(filename))
    out = open(filename, 'w')

    out.write("[require]\n")
    out.write("GLSL >= 1.10\n")
    out.write("\n")

    for stage, num in shaders:
        if stage == "vertex":
            out.write("[vertex shader]\n")
            out.write(shaders[(stage, num)])
        if stage == "fragment":
            out.write("[fragment shader]\n")
            out.write(shaders[(stage, num)])

    out.close()


def write_files(directory, shaders):
    for prog in shaders:
        write_shader_test("{0}/{1}.shader_test".format(directory, prog),
                          shaders[prog])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('appname', help='Output directory (application name)')
    parser.add_argument('mesadebug', help='MESA_GLSL=dump output file')
    args = parser.parse_args()

    dirname = "shaders/{0}".format(args.appname)
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

    infile = open(args.mesadebug, 'r')

    write_files(dirname, parse_input(infile.read()))


if __name__ == "__main__":
    main()
