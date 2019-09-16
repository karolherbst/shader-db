Shader-db: A collection of shaders for offline analysis
=======================================================

Shader-db is a giant pile of shaders from various apps, for whatever purpose.
In particular, we use it to capture assembly output of the shader compiler for
analysis of regressions in compiler behavior.

Currently it supports Mesa's i965 and radeonsi drivers.


## Capturing shaders

Create the directory for shader files

    $ mkdir dirpath

Write all shaders that are loaded by "executable" to the directory

    $ MESA_SHADER_CAPTURE_PATH=<dirpath> <executable>

Use `fdupes` can be used to remove duplicates

    $ fdupes -d <dirpath>


## Compiling

Some libraries are required when building. See section "Dependencies" below.
To build the binary, do:
make

## i965 Usage

### Running shaders

    $ ./run shaders 2> err | tee new-run

### To run just a subset:

    $ ./run shaders/supertuxkart 2> err | tee new-run

Make sure to check the contents of 'err' after your run.

To compile shaders for an i965 PCI ID different from your system, pass

	-p {i965,g4x,ilk,snb,ivb,hsw,byt,bdw}

to `run`.


### Analysis

    $ ./report.py old-run new-run


## radeonsi Usage

### Running shaders

    $ ./run shaders > new-run 2> /dev/null

Note that a debug mesa build required (ie. `--enable-debug`)


### Analysis

./si-report.py old-run new-run


## freedreno, v3d Usage

### Running shaders

    $ ./run shaders > new-run

Note that a debug mesa build required (ie. `--enable-debug`)

### Analysis

./report.py old-run new-run


## Dependencies

run requires some GNU C extensions, render nodes (/dev/dri/renderD128),
libepoxy, OpenMP, and Mesa configured with `--with-egl-platforms=x11,drm`


## jemalloc

Since run compiles shaders in different threads, malloc/free locking overhead
from inside Mesa can be expensive. Preloading jemalloc can cut significant
amounts of time:

    $ LD_PRELOAD=/usr/lib64/libjemalloc.so.1 ./run shaders 2> err | tee new-run


## Deprecated

`run.py` is obsolete. Use the `run` binary instead.


# Vulkan Fossils

shader-db also contains a selection of vulkan fossils. These are generated
using the fossilize.sh script and [fossil](https://github.com/ValveSoftware/Fossilize).

You will need a vulkan driver with pipeline statistics:

    $ fossilize-replay --enable-pipeline-stats output.csv --num-threads 4 fossils/**/*.foz

If you do not get a .csv file it likely means that a driver without
`VK_KHR_pipeline_statistics`, such as a system installed driver.

You can then compare two different csv files using the report-fossil.py script:

    $ report-fossil.py baseline.csv development.csv

## Capturing fossils

A fossilize.sh script is provided to assist in capturing fossils, you may
need to modify it based on where fossil lives on your system.
