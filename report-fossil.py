#!/usr/bin/env python3
# Copyright 2020 Valve Corporation

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

import sys
import csv
import typing
import importlib


def main():
    drivers: typing.Set[str] = set()

    for arg in sys.argv:
        if not arg.endswith('.csv'):
            continue
        with open(arg, 'rt') as f:
            reader = csv.reader(f)
            row = next(reader)
            if 'VGPRs' in row:
                drivers.add('radv')
            elif 'SEND Count' in row:
                drivers.add('anv')
            else:
                print('Cannot guess driver for %s' % arg)
                sys.exit(1)

    if len(drivers) == 0:
        print('No CSV files specified. Can\'t guess driver')
        sys.exit(1)
    if len(drivers) > 1:
        print('Results created from different drivers?')
        sys.exit(1)

    driver = next(iter(drivers))

    if driver == 'radv':
        importlib.import_module('radv-report-fossil').main()
    elif driver == 'anv':
        importlib.import_module('anv-report-fossil').main()


if __name__ == "__main__":
    main()

