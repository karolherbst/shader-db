#!/usr/bin/env python3

import re
import os
import argparse


def parse_input(infile):
    shaders = dict()
    programs = dict()
    shadertuple = ("bad", 0)
    prognum = ""
    reading = False
    is_glsl = True

    for line in infile.splitlines():
        declmatch = re.match(
            r"GLSL (.*) shader (.*) source for linked program (.*):", line)
        arbmatch = re.match(
            r"ARB_([^_]*)_program source for program (.*):", line)
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
            is_glsl = True
            print("Reading program {0} {1} shader {2}".format(
                prognum, shadertype, shadernum))
        elif arbmatch:
            shadertype = arbmatch.group(1)
            prognum = arbmatch.group(2)
            if prognum in programs:
                print("dupe!")
                exit(1)
            programs[prognum] = (shadertype, '')
            reading = True
            is_glsl = False
            print("Reading program {0} {1} shader".format(prognum, shadertype))
        elif re.match("GLSL IR for ", line):
            reading = False
        elif re.match("Mesa IR for ", line):
            reading = False
        elif re.match("GLSL source for ", line):
            reading = False
        elif reading:
            if is_glsl:
                shaders[prognum][shadertuple] += line + '\n'
            else:
                type, source = programs[prognum]
                programs[prognum] = (type, ''.join([source, line, '\n']))

    return (shaders, programs)


def write_shader_test(filename, shaders):
    print("Writing {0}".format(filename))
    out = open(filename, 'w')

    min_version = 110
    for stage, num in shaders:
        shader = shaders[(stage, num)]
        m = re.match(r"^#version (\d\d\d)", shader)
        if m:
            version = int(m.group(1), 10)
            if version > min_version:
                min_version = version

    out.write("[require]\n")
    out.write("GLSL >= %.2f\n" % (min_version / 100.))
    out.write("\n")

    for stage, num in shaders:
        if stage == "vertex":
            out.write("[vertex shader]\n")
        elif stage == "fragment":
            out.write("[fragment shader]\n")
        elif stage == "geometry":
            out.write("[geometry shader]\n")
        elif stage == "tess ctrl":
            out.write("[tessellation control shader]\n")
        elif stage == "tess eval":
            out.write("[tessellation evaluation shader]\n")
        else:
            assert False, stage
        out.write(shaders[(stage, num)])

    out.close()

def write_arb_shader_test(filename, type, source):
    print("Writing {0}".format(filename))
    out = open(filename, 'w')
    out.write("[require]\n")
    out.write("GL_ARB_{0}_program\n".format(type))
    out.write("\n")
    out.write("[{0} program]\n".format(type))
    out.write(source)
    # INTEL_DEBUG won't output anything for ARB programs unless you draw
    out.write("\n[test]\ndraw rect -1 -1 1 2\n");
    out.close()

def write_files(directory, shaders, programs):
    for prog in shaders:
        write_shader_test("{0}/{1}.shader_test".format(directory, prog),
                          shaders[prog])
    for prognum in programs:
        prog = programs[prognum]
        write_arb_shader_test("{0}/{1}p-{2}.shader_test".format(directory,
            prog[0][0], prognum), prog[0], prog[1])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('appname', help='Output directory (application name)')
    parser.add_argument('mesadebug', help='MESA_GLSL=dump output file')
    args = parser.parse_args()

    dirname = "shaders/{0}".format(args.appname)
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

    with open(args.mesadebug, 'r') as infile:
        shaders, programs = parse_input(infile.read())

    write_files(dirname, shaders, programs)

if __name__ == "__main__":
    main()
