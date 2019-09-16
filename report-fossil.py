#!/usr/bin/env python3
# Copyright © 2019 Intel Corporation

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

import argparse
import csv
import pathlib
import typing

import attr

if typing.TYPE_CHECKING:
    import typing_extensions

    class DiffProtocol(typing_extensions.Protocol):

        old: int
        new: int

    V = typing.TypeVar('V', int, float, str)


@attr.s(slots=True)
class Result:

    instructions: typing.Optional[int] = attr.ib()
    loops: typing.Optional[int] = attr.ib()
    cycles: typing.Optional[int] = attr.ib()
    spills: typing.Optional[int] = attr.ib()
    fills: typing.Optional[int] = attr.ib()


@attr.s(slots=True)
class ResultFactory:

    lookups: typing.Dict[str, int] = attr.ib()

    def __call__(self, row: typing.List[str]) -> Result:
        def get(name: str, type_: typing.Type['V']) -> typing.Optional['V']:
            try:
                v = row[self.lookups[name]]
            except (KeyError, IndexError):
                return None
            return type_(v)

        return Result(
            instructions=get('Instruction Count', int),
            loops=get('Loop Count', int),
            cycles=get('Cycle Count', int),
            spills=get('Spill Count', int),
            fills=get('Fill Count', int),
        )


def calculate_percent(diff: 'DiffProtocol') -> str:
    if diff.new and diff.old:
        return '{:+.1%}'.format((diff.new / diff.old) - 1)
    return '0.0%'


@attr.s(slots=True)
class ProgramDiff:

    name: str = attr.ib()
    old: int = attr.ib()
    new: int = attr.ib()


@attr.s(slots=True)
class Diff:

    name: str = attr.ib()
    old: int = attr.ib(0)
    new: int = attr.ib(0)
    helped: typing.Dict[str, ProgramDiff] = attr.ib(factory=dict)
    hurt: typing.Dict[str, ProgramDiff] = attr.ib(factory=dict)

    def generate(self) -> str:
        result: typing.List[str] = [
            f'{self.name} in all programs: {self.old} -> {self.new} ({calculate_percent(self)})']
        result.extend(
            [f'{self.name} helped {n}: {h.old} -> {h.new} ({calculate_percent(h)})'
             for n, h in self.helped.items()])
        result.extend(
            [f'{self.name} hurt {n}: {h.old} -> {h.new} ({calculate_percent(h)})'
             for n, h in self.hurt.items()])

        return '\n'.join(result)


@attr.s(slots=True)
class Report:

    instructions: Diff = attr.ib(factory=lambda: Diff('Instructions'))
    loops: Diff = attr.ib(factory=lambda: Diff('Loops'))
    cycles: Diff = attr.ib(factory=lambda: Diff('Cycles'))
    spills: Diff = attr.ib(factory=lambda: Diff('Spills'))
    fills: Diff = attr.ib(factory=lambda: Diff('Fills'))

    def include(self, name: str, d0: Result, d1: Result) -> None:
        for m in ['instructions', 'loops', 'cycles', 'spills', 'fills']:
            self._include(name, getattr(self, m), getattr(d0, m), getattr(d1, m))

    def _include(self, name: str, member: Diff, d0: typing.Optional[int],
                 d1: typing.Optional[int]) -> None:
        if not (d0 and d1):
            return

        if d0 > d1:
            member.helped[name] = ProgramDiff(name, d0, d1)
        elif d0 < d1:
            member.hurt[name] = ProgramDiff(name, d0, d1)

        member.old += d0
        member.new += d1

    def _include_cycles(self, name: str, d0: Result, d1: Result) -> None:
        pass

    def generate(self) -> str:
        return '\n\n'.join(m.generate() for m in attr.astuple(self, recurse=False))


def read_csv(csv_file: pathlib.Path) -> typing.Dict[str, Result]:
    data: typing.Dict[str, Result] = {}
    with csv_file.open('rt') as f:
        reader = csv.reader(f)
        factory = ResultFactory({k: v for v, k in enumerate(next(reader))})
        for row in reader:
            name = row[0]
            data[name] = factory(row)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', nargs=2, type=pathlib.Path, help='Path to CSV files')
    args = parser.parse_args()

    data0 = read_csv(args.csv[0])
    data1 = read_csv(args.csv[1])

    names = set(list(data0.keys()) + list(data1.keys()))

    report = Report()
    for name in names:
        d0 = data0.get(name)
        d1 = data1.get(name)
        if not (d0 and d1):
            # If a fossil is only in one run or another don't include it,
            # otherwise we'll skew the overall results.
            continue
        report.include(name, d0, d1)

    print(report.generate())


if __name__ == "__main__":
    main()

