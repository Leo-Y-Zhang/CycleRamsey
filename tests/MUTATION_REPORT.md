The new tests exercise witness verification first, then evidence validation,
model parsing/decoding, CNF semantics and serialization, cycle enumeration, and
symmetry breaking. Production Python files and stored evidence are unchanged;
no import seam or runtime dependency was needed.

`conftest.py` provides source imports. `.github/workflows/ci.yml` installs
`pytest==8.4.2` and runs one `pytest -q` step in the existing gate job.

Mutation measurement uses `mutation_check.py`: 63 selected substitutions,
applied individually to disposable copies under `/work`. Every substituted
module must compile. Each copy runs the original gate; the after measurement
also independently runs the new pytest suite, even when the gate already
killed the mutant. The unmutated checks must pass first. A check must exit
nonzero to kill a mutant; a timeout aborts measurement instead of counting as
a kill. Application files in the working tree are never mutated.

Before means the original solver-free gate (there were no unit tests).
After means that gate plus the new tests. The JSON files retain each exact
substitution and its individual command exit statuses. This is a targeted
mutation sample, not an exhaustive mutation score for every statement.

| Module | Mutants tried | Killed before | Killed after |
|---|---:|---:|---:|
| `ramsey/verify_witness.py` | 11 | 6 | 11 |
| `ramsey/verify_all.py` | 13 | 8 | 13 |
| `ramsey/encode.py` | 14 | 1 | 14 |
| `ramsey/cycles.py` | 6 | 6 | 6 |
| `ramsey/symmetry.py` | 6 | 2 | 6 |
| `ramsey/solve.py` | 8 | 0 | 8 |
| `ramsey/__main__.py` | 5 | 0 | 5 |
| **Total** | **63** | **23** | **63** |

Each new test file catches a specific mutation:

| Test file | Mutation killed and location | Relevant assertion |
|---|---|---|
| `test_verify_witness.py` | `verify_witness.find_cycle`: `length < 3` becomes `length <= 3` | A one-edge recolouring creating a triangle is rejected, for each of the three colours. |
| `test_encoding.py` | `encode.Encoding.colouring_from_model`: `len(assigned) != 1` becomes `< 1` | A model giving two colours to one edge raises `ValueError`. Also checks CNF truth on all 729 K4 colourings, missing colours, truncated models, and DIMACS counts/terminators. |
| `test_cycles_symmetry.py` | `symmetry.sorted_star_clauses`: `range(1, 3)` becomes `range(1, 2)` | Every three-edge star assignment satisfies the break exactly when its colours are sorted, including descending blue pairs. Also kills `cycle_edges` changing `i + 1` to `i + 2`. |
| `test_records.py` | `verify_all.record_problems`: timeout answer check changes `or` to `and` | A timeout carrying either a colouring or an answer by itself is rejected. Valid plain/symmetry and SAT/timeout records are accepted; removed-clause counts, missing fields, incorrect types, and uncertified verdicts are rejected. |
| `test_solve.py` | `solve.solve`: replace `check_colouring(n, colouring, targets)` with `pass` | A SAT return code with a complete monochromatic-triangle model still raises `AssertionError`. Solver calls are stubbed; valid models, truncation, multiple colours, parser literals, and status handling are checked without a solver. |
| `test_cli_check.py` | `__main__.cmd_check`: replace `if not good:` with `if False:` | Recolouring the valid `001` witness to `000` returns failure with `BAD`. Also checks accepted witnesses, wrong string counts, missing witnesses, invalid colours, truncated JSON, and the suspect-witness branch. |

Verification commands (run from `/work`):

| Command | Result |
|---|---|
| `python tests/mutation_check.py before` | Exit 0; 23/63 mutants killed by the original gate. |
| `/work/.venv/bin/python tests/mutation_check.py after` | Exit 0; 63/63 killed. The new pytest suite independently exits 1 for every mutant; the gate still kills the same 23. |
| `/work/.venv/bin/pytest -q` | Exit 0; complete output below. |
| `/work/.venv/bin/pytest -q --durations=5` | Exit 0; 108 passed in 1.71s; slowest individual duration 0.04s (setup), slowest test call 0.02s. |
| `python ramsey/verify_all.py` | Exit 0; 103 passed / 0 failed before changes. |
| `/work/.venv/bin/python ramsey/verify_all.py` | Exit 0; 103 passed / 0 failed after changes. |
| `/work/.venv/bin/ruff check .` | Exit 0; All checks passed! |
| `git diff --check` | Exit 0; no output. |

Complete `pytest -q` output:

```text
........................................................................ [ 66%]
....................................                                     [100%]
108 passed in 0.72s
```

Existing gate result:

```text
103 passed / 0 failed
EVERY CLAIM IN THIS REPOSITORY IS SUPPORTED BY EVIDENCE ON DISK.
```

All measurements used local Python 3.11.2; the CI configuration targets Python
3.13, which was not available locally. Tests use only tiny constructed inputs,
standard-library code, pytest, and mocked solver output. They run no SAT solver
and use no network. Package downloads were limited to the development checks:
pytest 8.4.2 and the repository's existing ruff pin, 0.16.1, in `/work/.venv`.
The initial system-Python pip command failed because pip was unavailable there;
creating the local venv and installing those packages succeeded.
