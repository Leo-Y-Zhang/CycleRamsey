import subprocess

import pytest

from ramsey import solve as solver


def test_parse_model_preserves_signed_literals_across_lines():
    output = 'c 123\ns SATISFIABLE\nv 1 -2 -3 0\nv 4 -5 -6\nv -7 8 -9 0\n'
    assert solver.parse_model(output) == [1, -2, -3, 4, -5, -6, -7, 8, -9]
    assert solver.parse_model('c no model\ns UNSATISFIABLE\n') == []


def test_malformed_model_token_is_rejected():
    with pytest.raises(ValueError):
        solver.parse_model('v 1 broken 0\n')


def stub_solver(monkeypatch, *, code=10, timeout=False, output='v 1 4 8 0\n'):
    monkeypatch.setattr(solver, 'find_kissat', lambda _explicit: '/unused/kissat')

    def fake_run(kissat, cnf, timeout=None):
        assert kissat == '/unused/kissat'
        assert cnf.endswith('.cnf')
        return result

    result = {'returncode': code, 'timeout': timeout, 'seconds': 0.1,
              'stdout': output, 'stderr': 'diagnostic'}
    monkeypatch.setattr(solver, 'run_kissat', fake_run)


def test_solve_accepts_verified_model_and_serializes_edge_order(monkeypatch, tmp_path):
    stub_solver(monkeypatch)
    rec = solver.solve(3, (3, 3, 3), workdir=tmp_path)
    assert rec['verdict'] == 'SAT_WITNESS_VERIFIED'
    assert rec['colouring'] == '001'
    assert rec['sat'] is True
    assert rec['returncode'] == 10
    assert (rec['vars'], rec['clauses'], rec['symmetry_clauses']) == (9, 15, 0)
    assert not list(tmp_path.glob('*.cnf'))


@pytest.mark.parametrize(('output', 'error'), [
    ('v 1 4 7 0\n', AssertionError),  # Complete model, forbidden triangle.
    ('v 1 4 0\n', ValueError),  # Truncated model, one edge is uncoloured.
    ('v 1 2 4 8 0\n', ValueError),  # Two colours on one edge.
    ('s SATISFIABLE\n', ValueError),  # SAT return code without a witness.
])
def test_sat_status_never_bypasses_witness_validation(monkeypatch, tmp_path, output, error):
    stub_solver(monkeypatch, output=output)
    with pytest.raises(error):
        solver.solve(3, (3, 3, 3), workdir=tmp_path)


@pytest.mark.parametrize(('code', 'timeout', 'verdict', 'sat'), [
    (20, False, 'UNSAT', False),
    (None, True, 'TIMEOUT', None),
    (0, False, 'SOLVER_FAILED', None),
    (1, False, 'SOLVER_FAILED', None),
])
def test_solve_reports_status_without_inventing_witness(monkeypatch, tmp_path,
                                                       code, timeout, verdict, sat):
    stub_solver(monkeypatch, code=code, timeout=timeout, output='')
    rec = solver.solve(3, (3, 3, 3), workdir=tmp_path, keep=True, break_symmetry=True)
    assert rec['verdict'] == verdict
    assert rec['returncode'] == code
    assert rec['timed_out'] is timeout
    assert 'colouring' not in rec
    if sat is None:
        assert 'sat' not in rec
    else:
        assert rec['sat'] is sat
    if verdict == 'SOLVER_FAILED':
        assert rec['stderr'] == 'diagnostic'
    assert (rec['clauses'], rec['symmetry_clauses']) == (18, 3)
    assert len(list(tmp_path.glob('*.cnf'))) == 1


def test_subprocess_timeout_is_reported_without_a_decision(monkeypatch):
    def expire(command, **kwargs):
        assert command == ['fake', '-q', 'input.cnf']
        assert kwargs['timeout'] == 0.01
        raise subprocess.TimeoutExpired(command, 0.01)

    monkeypatch.setattr(solver.subprocess, 'run', expire)
    result = solver.run_kissat('fake', 'input.cnf', timeout=0.01)
    assert result['returncode'] is None
    assert result['timeout'] is True
    assert result['stdout'] == result['stderr'] == ''
