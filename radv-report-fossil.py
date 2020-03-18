#!/usr/bin/env python3
#
# Copyright 2020 Valve Corporation
#
# Based in part on report-fossil.py which is:
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
import os
import os.path
import sys

import attr

if typing.TYPE_CHECKING:
    import typing_extensions

    class DiffProtocol(typing_extensions.Protocol):

        old: int
        new: int

    class ReportProtocol(typing_extensions.Protocol):

        num_shaders: int
        num_affected_shaders: int
else:
    class DiffProtocol:

        pass

    class ReportProtocol:

        pass

T = typing.TypeVar('T')

if os.isatty(sys.stdout.fileno()):
    set_red = '\033[31m'
    set_green = '\033[1;32m'
    set_yellow = '\033[1;33m'
    set_normal = '\033[0m'
else:
    set_red, set_green, set_yellow, set_normal = '', '', '', ''


@attr.s(frozen=True, slots=True)
class Statistic(typing.Generic[T]):

    internal_name : str = attr.ib()
    csv_names : typing.FrozenSet[str] = attr.ib(converter=frozenset)
    display_name : str = attr.ib()
    more_is_better : bool = attr.ib(False)
    is_hash : bool = attr.ib(False)


statistics = [
    Statistic(internal_name='sgprs', csv_names=['SGPRs'], display_name='SGPRs'),
    Statistic(internal_name='vgprs', csv_names=['VGPRs'], display_name='VGPRs'),
    Statistic(internal_name='spilled_sgprs', csv_names=['Spilled SGPRs'], display_name='SpillSGPRs'),
    Statistic(internal_name='spilled_vgprs', csv_names=['Spilled VGPRs'], display_name='SpillVGPRs'),
    Statistic(internal_name='priv_vgprs', csv_names=['PrivMem VGPRs'], display_name='PrivVGPRs'),
    Statistic(internal_name='code_size', csv_names=['Code size'], display_name='CodeSize'),
    Statistic(internal_name='lds', csv_names=['LDS size'], display_name='LDS'),
    Statistic(internal_name='scratch', csv_names=['Scratch size'], display_name='Scratch'),
    Statistic(internal_name='max_waves', csv_names=['Subgroups per SIMD'], display_name='MaxWaves', more_is_better=True),
    # These ones are ACO-specific.
    Statistic(internal_name='instrs', csv_names=['Instructions'], display_name='Instrs'),
    Statistic(internal_name='cycles', csv_names=['Busy Cycles'], display_name='Cycles'),
    Statistic(internal_name='vmem', csv_names=['VMEM Score'], display_name='VMEM', more_is_better=True),
    Statistic(internal_name='smem', csv_names=['SMEM Score'], display_name='SMEM', more_is_better=True),
    Statistic(internal_name='vclause', csv_names=['VMEM Clause'], display_name='VClause'),
    Statistic(internal_name='sclause', csv_names=['SMEM Clause'], display_name='SClause'),
    Statistic(internal_name='hash', csv_names=['Hash'], display_name='Hash', is_hash=True),
    Statistic(internal_name='copies', csv_names=['Copies'], display_name='Copies'),
    Statistic(internal_name='branches', csv_names=['Branches'], display_name='Branches'),
    Statistic(internal_name='pre_sgprs', csv_names=['Pre-Sched SGPRs'], display_name='PreSGPRs'),
    Statistic(internal_name='pre_vgprs', csv_names=['Pre-Sched VGPRs'], display_name='PreVGPRs'),
]


executables = {
    'Vertex Shader' : 'vs',
    'Vertex + Tessellation Control Shaders' : 'vs_tcs',
    'Tessellation Control Shader' : 'tcs',
    'Tessellation Evaluation Shader' : 'tes',
    'Tessellation Evaluation + Geometry Shaders' : 'tes_gs',
    'Vertex + Geometry Shader' : 'vs_gs',
    'Geometry Shader' : 'gs',
    'Fragment Shader' : 'fs',
    'Compute Shader' : 'cs',
    'GS Copy Shader' : 'gs_copy',
}


@attr.s(slots=True, these={stat.internal_name :
                           attr.ib(type=typing.Optional[int], default=None) for stat in statistics})
class Result:

    pass


@attr.s(slots=True)
class ResultFactory:

    column_to_stat: typing.List[typing.Optional[Statistic]] = attr.ib()

    @classmethod
    def from_column_names(cls, column_names: typing.List[str],
                          inc_statistics: typing.Optional[typing.Set[Statistic]]):
        column_to_stat = []
        for name in column_names:
            def filter_fn(stat):
                if inc_statistics and stat not in inc_statistics:
                    return False
                return name in stat.csv_names
            column_to_stat.append(next(filter(filter_fn, statistics), None))
        return cls(column_to_stat)

    def __call__(self, row: typing.List[str]) -> Result:
        result = Result()
        for i, v in enumerate(row):
            stat = self.column_to_stat[i]
            if stat and v != '':
                setattr(result, stat.internal_name, int(v))

        return result


def calculate_delta(diff: 'DiffProtocol', stat:Statistic, spec:str = '{}') -> str:
    color = set_normal
    if diff.new != diff.old:
        if (diff.new > diff.old) == stat.more_is_better:
            color = set_green
        else:
            color = set_red

    return color + spec.format(diff.new - diff.old) + set_normal

def calculate_percent(diff: 'DiffProtocol', stat:Statistic, spec:str = '{}') -> str:
    color = set_normal
    if diff.new != diff.old:
        if (diff.new > diff.old) == stat.more_is_better:
            color = set_green
        else:
            color = set_red

    res = ''
    if diff.new == diff.old:
        res = '   .'
    elif diff.new and diff.old:
        res = '{:+.2%}'.format((diff.new / diff.old) - 1)
    elif not diff.old and not diff.new:
        res = '0.0%'
    elif not diff.old:
        res = '+inf%'
    elif not diff.new:
        res = '-inf%'
    return color + spec.format(res) + set_normal


def print_yellow(str):
    print(set_yellow + str + set_normal)


@attr.s(slots=True)
class ProgramDiff(DiffProtocol):

    name: str = attr.ib()
    old: int = attr.ib()
    new: int = attr.ib()


@attr.s(slots=True)
class Diff(DiffProtocol):

    stat: Statistic = attr.ib()
    old: int = attr.ib(0)
    new: int = attr.ib(0)
    old_affected: int = attr.ib(0)
    new_affected: int = attr.ib(0)
    helped: typing.Dict[str, ProgramDiff] = attr.ib(factory=dict)
    hurt: typing.Dict[str, ProgramDiff] = attr.ib(factory=dict)

    def get_only_affected(self):
        return Diff(stat = self.stat,
                    old = self.old_affected,
                    new = self.new_affected,
                    old_affected = self.old_affected,
                    new_affected = self.new_affected,
                    helped = self.helped,
                    hurt = self.hurt)

    def is_nonempty(self):
        return bool(self.helped) or bool(self.hurt)


report_attrs: typing.Dict[str, object] = {}
for stat in statistics:
    if stat.is_hash:
        continue
    # mypy can't infer the type of the lambda if I try to use one instead
    def factory(stat=stat):
        return Diff(stat)
    report_attrs[stat.internal_name] = attr.ib(factory=factory)
# https://github.com/python-attrs/attrs/issues/621
report_attrs['num_shaders'] = attr.ib(0, type=int)
report_attrs['num_affected_shaders'] = attr.ib(0, type=int)
@attr.s(slots=True, these=report_attrs)
class Report(ReportProtocol):

    def include(self, name: str, d0: Result, d1: Result) -> None:
        self.num_shaders += 1

        affected = False
        stats: typing.List[typing.Tuple[Diff, int, int]] = []
        for stat in statistics:
            m = stat.internal_name
            d0_m: typing.Optional[int] = getattr(d0, m)
            if d0_m is None:
                continue
            d1_m: typing.Optional[int] = getattr(d1, m)
            if d1_m is None:
                continue

            if stat.is_hash:
                affected = affected or d0_m != d1_m
                continue

            member: Diff = getattr(self, m)
            member.old += d0_m
            member.new += d1_m

            stats.append((member, d0_m, d1_m))
            if d0_m != d1_m:
                if (d1_m > d0_m) == member.stat.more_is_better:
                    member.helped[name] = ProgramDiff(name, d0_m, d1_m)
                else:
                    member.hurt[name] = ProgramDiff(name, d0_m, d1_m)

                affected = True

        if affected:
            self.num_affected_shaders += 1
            for member, d0_m, d1_m in stats:
                member.old_affected += d0_m
                member.new_affected += d1_m

    def get_diffs(self) -> typing.List[Diff]:
        return [getattr(self, stat.internal_name) for stat in statistics if hasattr(self, stat.internal_name)]

    def get_only_affected(self):
        diffs = {}
        for diff in self.get_diffs():
            diffs[diff.stat.internal_name] = diff.get_only_affected()
        return Report(num_shaders = self.num_affected_shaders,
                      num_affected_shaders = self.num_affected_shaders,
                      **diffs)


def read_csv(csv_file: pathlib.Path, inc_statistics: typing.Optional[typing.Set[Statistic]],
             all_apps: typing.Set[str]) -> typing.Dict[typing.Tuple[str, str], Result]:
    data: typing.Dict[typing.Tuple[str, str], Result] = {}

    with csv_file.open('rt') as f:
        reader = csv.reader(f)
        for row in reader:
            if 'Database' in row:
                factory = ResultFactory.from_column_names(row, inc_statistics)
                db_index = row.index('Database')
                hash_index = row.index('Pipeline hash')
                exec_index = row.index('Executable name')
                continue

            app = row[db_index]
            all_apps.add(app)
            name = '{}/{}'.format(row[hash_index], executables[row[exec_index]])
            data[(app, name)] = factory(row)

    return data


def shorten_app_names(apps: typing.Set[str]) -> typing.Dict[str, str]:
    def would_cause_ambiguity(old_name: str, new_name: str, all_names, process):
        return any(process(other) == new_name for other in all_names if other != old_name)

    def simplify_app_names(mapping: typing.Dict[str, str], process):
        while True:
            new_app_names: typing.Dict[str, str] = {}
            for old, cur in mapping.items():
                new = process(cur)
                if new != cur and not would_cause_ambiguity(cur, new, mapping.values(), process):
                    new_app_names[old] = new
            mapping.update(new_app_names)
            if len(new_app_names) == 0:
                break

    # Remove hash and extension if it's not useful.
    app_mapping = {app : app for app in apps}
    def remove_hash_extension(name: str) -> str:
        head, tail = os.path.split(name)
        return os.path.join(head, tail.rsplit('.', 1)[0])
    simplify_app_names(app_mapping, remove_hash_extension)

    # Remove common base directory.
    if len(app_mapping) > 1:
        common_path = os.path.commonpath(list(app_mapping.values()))
        app_mapping = {old : new[len(common_path):].lstrip('/') for old, new in app_mapping.items()}
    elif len(app_mapping) == 1:
        app_mapping = {old : os.path.split(new)[1] for old, new in app_mapping.items()}

    return app_mapping


def compare_results(report: Report) -> None:
    for m in report.get_diffs():
        if m.old == m.new:
            continue

        split = ''
        if m.helped and m.hurt:
            split = '; split: '

            total_helped = ProgramDiff('', old=m.old, new=m.old)
            for helped in m.helped.values():
                total_helped.new += helped.new - helped.old
            split += '{}'.format(calculate_percent(total_helped, m.stat))

            total_hurt = ProgramDiff('', old=m.old, new=m.old)
            for hurt in m.hurt.values():
                total_hurt.new += hurt.new - hurt.old
            split += ', {}'.format(calculate_percent(total_hurt, m.stat))

        print('{}: {} -> {} ({}){}'.format(
            m.stat.display_name, m.old, m.new, calculate_percent(m, m.stat), split))
    print('')


def print_best_worst(results: typing.Dict[str, Result], name: str, worst: bool):
    stat = next(filter(lambda stat: name.lower() == stat.display_name.lower(), statistics), None)
    if not stat:
        return

    cond = lambda v: getattr(v[1], stat.internal_name) is not None
    key = lambda v: getattr(v[1], stat.internal_name)
    items = sorted(filter(cond, results.items()), key = key, reverse = stat.more_is_better != worst)[:40]

    name_col_size = max((len(item[0]) for item in items), default=0) + 5
    fmt = ' {{:{}}}{{}}'.format(name_col_size)

    for name, result in items:
        print(fmt.format(name, getattr(result, stat.internal_name)))
    print('')


def print_table_row(name: str, row_fmt: str, app_cell_width: int, cell_width: int,
                    statistics: typing.Set[Statistic], report: Report):
    cols = [name, report.num_shaders]
    for diff in report.get_diffs():
        if diff.stat in statistics:
            cols.append(calculate_percent(diff, diff.stat, '{{:{}}}'.format(cell_width)))
    print(row_fmt.format(*cols))

def print_tables(total: Report, apps: typing.Dict[str, Report]):
    stats_needed = set()
    for diff in total.get_diffs():
        if diff.old != diff.new:
            stats_needed.add(diff.stat)

    longest_app_name = max((len(name) for name in apps.keys()), default=0)
    app_cell_width = max(len('PERCENTAGE DELTAS'), longest_app_name) + 1

    cell_width = max((len(stat.display_name) for stat in stats_needed), default=0)
    cell_width = max(cell_width, len('+999.99%')) + 1

    row_fmt = ' {{:<{}}}'.format(app_cell_width)
    row_fmt += '{{:<{}}}'.format(cell_width) * (len(stats_needed) + 1)
    legend = row_fmt.format(*(['PERCENTAGE DELTAS', 'Shaders'] + [m.stat.display_name for m in total.get_diffs() if m.stat in stats_needed]))

    i = 0
    num_spacing = max(1, len(apps.items()) // 20)
    spacing = (len(apps.items()) + num_spacing - 1) // num_spacing
    for name, app in sorted(apps.items(), key=lambda v: v[0]):
        if i % spacing == 0:
            print_yellow(legend)
        print_table_row(name, row_fmt, app_cell_width, cell_width, stats_needed, app);
        i += 1
    if len(apps) == 0:
        print_yellow(' ' + legend)
    print(' ' + '-' * len(legend))
    print_table_row('All affected', row_fmt, app_cell_width, cell_width, stats_needed, total.get_only_affected());
    print(' ' + '-' * len(legend))
    print_table_row('Total', row_fmt, app_cell_width, cell_width, stats_needed, total);
    print('')


def print_changes(title: str, report: Report, helped: bool, hurt: bool, name: str, sort):

    stat = next(filter(lambda stat: name.lower() == stat.display_name.lower(), statistics), None)
    if not stat:
        return

    diffs = getattr(report, stat.internal_name)
    changes: typing.List[ProgramDiff] = []
    if helped:
        changes += diffs.helped.values()
    if hurt:
        changes += diffs.hurt.values()
    changes = sorted(changes, key = lambda v: sort(v.new, v.old, v.name), reverse = True)[:40]

    name_col_size = max((len(diff.name) for diff in changes), default=0)
    name_col_size = max(name_col_size, len(title), 32) + 5

    print_yellow(' {{:{}}}Before     After      Delta      Percentage'.format(name_col_size).format(title))

    for diff in changes:
        print(' {{:{}}}{{:<11}}{{:<11}}{{}}{{}}'.format(name_col_size).format(diff.name, diff.old, diff.new,
              calculate_delta(diff, stat, '{:<+11}'), calculate_percent(diff, stat, '{:<11}')))
    print('')


def print_affected_shaders(names: typing.Set[str], before: typing.Dict[str, Result], after: typing.Dict[str, Result]):
    affected = []
    for name in names:
        before_res = before.get(name)
        after_res = after.get(name)
        assert before_res and after_res
        if attr.astuple(before_res, recurse=False) !=\
           attr.astuple(after_res, recurse=False):
            before_size = getattr(before_res, 'code_size', None) or 999999
            after_size = getattr(after_res, 'code_size', None) or 999999
            affected.append((name, max(before_size, after_size)))

    key = lambda v: v[1]
    count = 0
    for name, code_size in sorted(affected, key = key):
        print(' {}'.format(name))
        count += 1
        if count > 40:
            break
    print('')


def print_affected_apps(apps: typing.Dict[str, Report]):
    affected: typing.Set[str] = set()
    for name, app in apps.items():
        for diff in app.get_diffs():
            if diff.old != diff.new:
                affected.add(name)
                break

    for app_name in sorted(affected):
        print(' {}'.format(app_name))
    print('')


def report_ignored(names: typing.List[str], what: str):
    if not names:
        return
    print('*** {} are ignored:'.format(what))
    msg = ', '.join(names[:5])
    if len(names) > 5:
        msg += ', and {} more'.format(len(names) - 5)
    print(msg)

    apps: typing.Set[str] = set()
    for name in names:
        apps.add(name.rsplit('/', 2)[0])
    app_list: typing.List[str] = sorted(apps)
    msg = 'from {} apps: {}'.format(len(app_list), ', '.join(app_list[:7]))
    if len(app_list) > 7:
        msg += '...'
    print(msg)

    print('')


def get_stat_list(names: typing.Optional[typing.List[str]], all_stats: typing.List[str]):
    if names == []:
        return all_stats
    return names or []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', nargs='+', type=pathlib.Path, help='Path to CSV files')
    stat_list_arg = {'nargs':'*', 'default':None, 'type':str, 'metavar':'STAT',
                     'choices':[stat.display_name for stat in statistics if not stat.is_hash]}
    parser.add_argument('--apps', nargs='+', type=str, metavar='NAME', help='Only consider certain applications')
    parser.add_argument('--stats', **stat_list_arg, help='Only consider certain statistics')
    parser.add_argument('--rel-changes', **stat_list_arg, help='Show improvements sorted by relative change')
    parser.add_argument('--abs-changes', **stat_list_arg, help='Show improvements sorted by absolute change')
    parser.add_argument('--rel-small-changes', **stat_list_arg, help='Show improvements sorted by relative change divided by code size')
    parser.add_argument('--affected', action='store_const', const=True, help='Show affected shaders sorted by code size')
    parser.add_argument('--affected-apps', action='store_const', const=True, help='Show affected applications')
    parser.add_argument('--worst', **stat_list_arg, help='Show shaders which are worst')
    parser.add_argument('--best', **stat_list_arg, help='Show shaders which are best')
    parser.add_argument('--hide-table', action='store_const', const=True, help='Hide the table')
    args = parser.parse_args()

    inc_statistics = None
    if args.stats:
        inc_statistics = set(stat for stat in statistics if stat.display_name in args.stats)

    all_apps: typing.Set[str] = set()
    before = read_csv(args.csv[0], inc_statistics, all_apps)
    after = read_csv(args.csv[1], inc_statistics, all_apps) if len(args.csv) >= 2 else None

    app_mapping = shorten_app_names(all_apps)
    app_filter = args.apps or app_mapping.values()
    before = {'{}/{}'.format(app_mapping[k[0]], k[1]) : v for k, v in before.items() if app_mapping[k[0]] in app_filter}
    if after:
        after = {'{}/{}'.format(app_mapping[k[0]], k[1]) : v for k, v in after.items() if app_mapping[k[0]] in app_filter}

    before_names = set(before.keys())

    names = set(before_names)
    if after:
        after_names = set(after.keys())

        # If a shader is only in one run or another don't include it,
        # otherwise we'll skew the overall results.
        names.intersection_update(after_names)

        only_in_after = list(after_names.difference(before_names))
        only_in_before = list(before_names.difference(after_names))
        report_ignored(only_in_after, 'Shaders only in \'after\' results')
        report_ignored(only_in_before, 'Shaders only in \'before\' results')

    if after is not None:
        apps = {}
        total = Report()
        for name in names:
            d0 = before.get(name)
            d1 = after.get(name)
            app = apps.setdefault(name.rsplit('/', 2)[0], Report())
            app.include(name, d0, d1)
            total.include(name, d0, d1)

        print('Totals:')
        compare_results(total)

        print('Totals from {} ({:.2%} of {}) affected shaders:'.format(
            total.num_affected_shaders,
            total.num_affected_shaders / max(1, total.num_shaders),
            total.num_shaders))
        compare_results(total.get_only_affected())

        affected_stats = [stat.display_name for stat in statistics if
                          hasattr(total, stat.internal_name) and
                          getattr(total, stat.internal_name).is_nonempty()]

        for name in get_stat_list(args.rel_changes, affected_stats):
            print_changes('RELATIVE IMPROVEMENTS - {}'.format(name),
                          total, True, False, name, lambda old, new, name: abs(new / max(old, 0.0001) - 1.0))

            print_changes('RELATIVE REGRESSIONS - {}'.format(name),
                          total, False, True, name, lambda old, new, name: abs(new / max(old, 0.0001) - 1.0))

        for name in get_stat_list(args.abs_changes, affected_stats):
            print_changes('ABSOLUTE IMPROVEMENTS - {}'.format(name),
                          total, True, False, name, lambda old, new, name: abs(new - old))

            print_changes('ABSOLUTE REGRESSIONS - {}'.format(name),
                          total, False, True, name, lambda old, new, name: abs(new - old))

        for name in get_stat_list(args.rel_small_changes, affected_stats):
            key = lambda old, new, name: abs(new / max(old, 0.0001) - 1.0) / max(before.get(name).code_size, after.get(name).code_size)

            print_changes('SMALL RELATIVE IMPROVEMENTS - {}'.format(name),
                          total, True, False, name, key)

            print_changes('SMALL RELATIVE REGRESSIONS - {}'.format(name),
                          total, False, True, name, key)

        if args.affected:
            print_yellow(' AFFECTED SHADERS')
            print_affected_shaders(names, before, after)

        if args.affected_apps:
            print_yellow(' AFFECTED APPLICATIONS')
            print_affected_apps(apps)

        if not args.hide_table:
            print_tables(total, apps)

    for name in get_stat_list(args.worst, [stat.display_name for stat in statistics]):
        print_yellow(' WORST SHADERS - {}'.format(name))
        print_best_worst(before, name, True)

    for name in get_stat_list(args.best, [stat.display_name for stat in statistics]):
        print_yellow(' BEST SHADERS - {}'.format(name))
        print_best_worst(before, name, False)


if __name__ == '__main__':
    main()

