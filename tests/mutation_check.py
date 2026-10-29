"""Targeted, one-at-a-time mutations; run from the repository root.

python tests/mutation_check.py before
python tests/mutation_check.py after

Only disposable copies under /work are edited. A mutant is killed only by a
nonzero check exit, never by a timeout. Results retain the exact substitution
and separate gate/pytest statuses. No solver or network is used.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = []


def mutations(module, replacements):
    for label, old, new in replacements:
        MUTANTS.append((f'{module}:{label}', f'ramsey/{module}.py', old, new))


mutations('verify_witness', [
    ('triangle-boundary', 'length < 3 or length > n', 'length <= 3 or length > n'),
    ('spanning-boundary', 'length < 3 or length > n', 'length < 3 or length >= n'),
    ('omit-reverse-adjacency', 'adj[w].add(u)', 'pass'),
    ('accept-open-path', 'return list(path) if start in adj[path[-1]] else None',
     'return list(path)'),
    ('walk-guard-and', 'nxt <= start or nxt in seen', 'nxt <= start and nxt in seen'),
    ('accept-extra-edge', 'len(colouring) != expected', 'len(colouring) < expected'),
    ('wrong-edge-count', 'n * (n - 1) // 2', 'n * (n + 1) // 2'),
    ('skip-missing-edge', 'if (u, w) not in colouring:', 'if False:'),
    ('accept-invalid-colour', 'if colouring[(u, w)] not in (0, 1, 2):', 'if False:'),
    ('accept-forbidden-cycle', 'if found is not None:\n            raise AssertionError',
     'if False:\n            raise AssertionError'),
    ('is-good-swallow-rejection', 'except AssertionError:\n        return False',
     'except AssertionError:\n        return True'),
])
mutations('verify_all', [
    ('same-ignore-type', 'type(value) is type(expected) and value == expected',
     'value == expected'),
    ('ignore-name', 'if name != stem:', 'if False:'),
    ('ignore-problem', "if rec.get('problem') != f'R(C{a},C{b},C{c})':", 'if False:'),
    ('ignore-encoding', "if rec.get('encoding') != encoding:", 'if False:'),
    ('ignore-symmetry-count', "if not same(rec.get('symmetry_clauses', 0), extra):", 'if False:'),
    ('ignore-variable-count', "if not same(rec.get('vars'), 3 * m):", 'if False:'),
    ('ignore-clause-count', "if not same(rec.get('clauses'), clauses):", 'if False:'),
    ('sat-any-field', 'if not all(same(rec.get(k), v) for k, v in',
     'if not any(same(rec.get(k), v) for k, v in'),
    ('sat-no-witness', "if 'colouring' not in rec:", 'if False:'),
    ('timeout-and', "rec.get('returncode') is not None or rec.get('timed_out') is not True",
     "rec.get('returncode') is not None and rec.get('timed_out') is not True"),
    ('timeout-ignore-flag', "rec.get('returncode') is not None or rec.get('timed_out') is not True",
     "rec.get('returncode') is not None"),
    ('timeout-answer-and', "if 'sat' in rec or 'colouring' in rec:",
     "if 'sat' in rec and 'colouring' in rec:"),
    ('accept-uncertified-verdict',
     'problems.append(f\'verdict {verdict!r} is not one this gate can re-check\')', 'pass'),
])
mutations('encode', [
    ('accept-target-arity', 'if len(targets) != NUM_COLOURS:', 'if False:'),
    ('reject-triangles', 'if any(t < 3 for t in targets):', 'if any(t <= 3 for t in targets):'),
    ('zero-based-vars', 'self.edge_index[edge] + colour + 1', 'self.edge_index[edge] + colour + 0'),
    ('colour-sign', 'self.edge_index[edge] + colour + 1', 'self.edge_index[edge] - colour + 1'),
    ('at-least-one-sign', '[self.var(e, c) for c in range(NUM_COLOURS)]',
     '[-self.var(e, c) for c in range(NUM_COLOURS)]'),
    ('at-most-one-sign', '[-self.var(e, c1), -self.var(e, c2)]',
     '[-self.var(e, c1), self.var(e, c2)]'),
    ('cycle-clause-sign', '[-self.var(e, colour) for e in cycle_edges(cyc)]',
     '[self.var(e, colour) for e in cycle_edges(cyc)]'),
    ('cycle-clause-truncated', 'for e in cycle_edges(cyc)]', 'for e in cycle_edges(cyc)[:-1]]'),
    ('model-negative-literals', 'if v > 0}', 'if v < 0}'),
    ('model-accept-multiple', 'if len(assigned) != 1:', 'if len(assigned) < 1:'),
    ('model-accept-missing', 'if len(assigned) != 1:', 'if len(assigned) > 1:'),
    ('dimacs-variable-count', '{self.num_vars} {len(self.clauses)}',
     '{self.num_vars + 1} {len(self.clauses)}'),
    ('dimacs-clause-count', '{self.num_vars} {len(self.clauses)}',
     '{self.num_vars} {len(self.clauses) - 1}'),
    ('dimacs-no-terminator', "fh.write(' 0\\n')", "fh.write('\\n')"),
])
mutations('cycles', [
    ('omit-triangles', 'if length < 3 or length > n:', 'if length <= 3 or length > n:'),
    ('omit-spanning-cycles', 'if length < 3 or length > n:', 'if length < 3 or length >= n:'),
    ('duplicate-orientations', 'if tail[0] < tail[-1]:', 'if True:'),
    ('double-count', 'factorial(length - 1) // 2', 'factorial(length - 1) // 1'),
    ('skip-cycle-neighbour', '(i + 1) % len(cycle)', '(i + 2) % len(cycle)'),
    ('omit-last-vertex', 'combinations(range(n), 2)', 'combinations(range(n - 1), 2)'),
])
mutations('symmetry', [
    ('forbid-equal-colours', 'for lo in range(hi):', 'for lo in range(hi + 1):'),
    ('omit-blue-comparisons', 'for hi in range(1, 3):', 'for hi in range(1, 2):'),
    ('comparison-sign', '[-enc.var(a, hi), -enc.var(b, lo)]',
     '[-enc.var(a, hi), enc.var(b, lo)]'),
    ('do-not-apply', 'enc.clauses.extend(extra)', 'pass'),
    ('reverse-star', 'key=lambda v: colouring[tuple(sorted((0, v)))]',
     'key=lambda v: -colouring[tuple(sorted((0, v)))]'),
    ('mapping-off-by-one', 'enumerate(order, start=1)', 'enumerate(order, start=0)'),
])
mutations('solve', [
    ('parse-status-as-model', "line.startswith('v ')", "line.startswith('s ')"),
    ('parse-only-zero', 'if x != 0]', 'if x == 0]'),
    ('drop-negative-literals', 'if x != 0]', 'if x > 0]'),
    ('invert-timeout', "if result['timeout']:", "if not result['timeout']:"),
    ('invert-unsat', "elif result['returncode'] == UNSAT:", "elif result['returncode'] != UNSAT:"),
    ('invert-sat', "elif result['returncode'] == SAT:", "elif result['returncode'] != SAT:"),
    ('skip-witness-verification', 'check_colouring(n, colouring, targets)', 'pass'),
    ('serialize-wrong-order', 'str(colouring[e]) for e in enc.edges',
     'str(colouring[e]) for e in reversed(enc.edges)'),
])
mutations('__main__', [
    ('check-length-inverted', 'if len(raw) != len(order):', 'if len(raw) == len(order):'),
    ('check-length-off-by-one', 'if len(raw) != len(order):', 'if len(raw) < len(order):'),
    ('check-accept-bad', 'if not good:', 'if False:'),
    ('check-no-witness', 'if raw is None:', 'if False:'),
    ('check-accept-suspect', 'if not broke:', 'if False:'),
])


def run(command, directory):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    result = subprocess.run(command, cwd=directory, env=env, capture_output=True,
                            text=True, timeout=20)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('before', 'after'))
    args = parser.parse_args()
    output = ROOT / 'tests' / f'mutation_{args.phase}.json'
    results = []
    with tempfile.TemporaryDirectory(prefix='.mutation-', dir=ROOT) as directory:
        directory = Path(directory)
        shutil.copytree(ROOT / 'ramsey', directory / 'ramsey',
                        ignore=shutil.ignore_patterns('__pycache__'))
        if args.phase == 'after':
            shutil.copytree(ROOT / 'tests', directory / 'tests',
                            ignore=shutil.ignore_patterns('__pycache__'))
        gate = [sys.executable, 'ramsey/verify_all.py']
        pytest = [sys.executable, '-m', 'pytest', '-q', '-x', 'tests']
        assert run(gate, directory) == 0, 'unmutated gate failed'
        if args.phase == 'after':
            assert run(pytest, directory) == 0, 'unmutated tests failed'
        for label, module, old, new in MUTANTS:
            path = directory / module
            original = path.read_text()
            assert old in original, (label, old)
            # The first occurrence is deliberate (e.g. cycles' generator guard).
            mutated = original.replace(old, new, 1)
            compile(mutated, module, 'exec')
            try:
                path.write_text(mutated)
                gate_status = run(gate, directory)
                test_status = run(pytest, directory) if args.phase == 'after' else None
            finally:
                path.write_text(original)
            killed = gate_status != 0 or test_status not in (None, 0)
            results.append(dict(id=label, module=module, old=old, new=new,
                                gate_status=gate_status, pytest_status=test_status,
                                killed=killed))
            print(f'{label}: {"KILLED" if killed else "SURVIVED"}', flush=True)
    output.write_text(json.dumps(results, indent=2) + '\n')
    print(f'{sum(r["killed"] for r in results)}/{len(results)} killed; {output.name}')


if __name__ == '__main__':
    main()
