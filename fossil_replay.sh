#!/usr/bin/env bash
# Copyright © 2020 Valve Corporation

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Usage: fossil_replay.sh fossils/ output.csv <arguments to pass to fossilize-replay>
# Runs each app in a separate fossilize-replay process as recommended and to
# handle separate Vulkan version requirements.
IFS=$'\n'
rm -f "$2" /tmp/fossil_replay.txt
for db in `find -L "$1" -type f -name "*.foz"`; do
    if [ ! $printed_name ]; then
        # Print the device name
        fossilize-replay ${@:3} "$db" --graphics-pipeline-range 0 0 --compute-pipeline-range 0 0 2>&1 | grep "Chose GPU:" -A1
        printed_name=1
    fi

    # Append stdout/stderr to file to reduce spam
    echo "Replaying $db"
    echo "Replaying $db" >> "/tmp/fossil_replay.txt"
    rm -f "$2".tmp
    fossilize-replay --enable-pipeline-stats "$2".tmp ${@:3} "$db" 1>&2 2>> "/tmp/fossil_replay.txt"

    # Check for failures
    if [ ! -e "$2".tmp ]; then
        rm -f "$2".tmp.__tmp.foz
        echo "Replay of $db failed"
        grep "pipeline crashed or hung" /tmp/fossil_replay.txt
        exit 1
    fi

    # Append to result CSV
    cat "$2".tmp >> "$2"
done
rm -f "$2".tmp
