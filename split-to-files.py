#!/usr/bin/env python3

from getopt import getopt, GetoptError
import re
import sys
import os

def usage():
    USAGE = """\
Usage: %(progName)s <appname> <mesadebug.log>

Options:
  -h, --help                Show this message
"""
    print(USAGE % {'progName': sys.argv[0]})
    sys.exit(1)

def parse_input(input):
    shaders = dict()
    shadertuple = ("bad", 0)
    prognum = ""
    reading = False

    for line in input.splitlines():
        declmatch = re.match("GLSL (.*) shader (.*) source for linked program (.*):", line)
        if declmatch:
            shadertype = declmatch.group(1)
            shadernum = declmatch.group(2)
            prognum = declmatch.group(3)
            shadertuple = (shadertype, shadernum)

            # don't save driver-internal shaders.
            if prognum == "0":
                continue

            if not prognum in shaders:
                shaders[prognum] = dict()
            if shadertuple in shaders[prognum]:
                print("dupe!")
                exit(1)
            shaders[prognum][shadertuple] = ''
            reading = True
            print("Reading program {0} {1} shader {2}".format(prognum, shadertype, shadernum))
        elif re.match("GLSL IR for ", line):
            reading = False
        elif re.match("GLSL source for ", line):
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

    for (type, num) in shaders:
        if type == "vertex":
            out.write("[vertex shader]\n")
            out.write(shaders[(type, num)])
        if type == "fragment":
            out.write("[fragment shader]\n")
            out.write(shaders[(type, num)])

    out.close()

def write_files(dir, shaders):
    for prog in shaders:
        write_shader_test("{0}/{1}.shader_test".format(dir, prog), shaders[prog])

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

    if len(args) != 2:
        usage()

    dirname = "shaders/{0}".format(args[0])
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

    input = open(args[1], 'r')

    write_files(dirname, parse_input(input.read()))

if __name__ == "__main__":
        main()
