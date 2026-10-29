import pytest

from ramsey.verify_all import record_problems, same


def record(*, broken=False, timeout=False):
    result = {
        'n': 3, 'targets': [3, 3, 3], 'problem': 'R(C3,C3,C3)',
        'vars': 9, 'clauses': 18 if broken else 15,
        'encoding': ('one-hot, sorted-star symmetry break' if broken
                     else 'one-hot, no symmetry breaking'),
        'symmetry_clauses': 3 if broken else 0,
        'verdict': 'TIMEOUT' if timeout else 'SAT_WITNESS_VERIFIED',
        'returncode': None if timeout else 10, 'timed_out': timeout,
    }
    if not timeout:
        result.update(sat=True, colouring='001')
    return result


@pytest.mark.parametrize('broken', [False, True])
@pytest.mark.parametrize('timeout', [False, True])
def test_consistent_records_are_accepted(broken, timeout):
    name = '3-3-3_n3_sb.json' if broken else '3-3-3_n3.json'
    assert record_problems(name, record(broken=broken, timeout=timeout)) == []


@pytest.mark.parametrize(('field', 'value', 'reason'), [
    ('problem', 'R(C3,C3,C4)', 'problem'),
    ('encoding', 'one-hot, sorted-star symmetry break', 'encoding'),
    ('symmetry_clauses', 1, 'symmetry clauses'),
    ('vars', 8, 'variables'),
    ('vars', 9.0, 'variables'),
    ('clauses', 14, 'clauses'),  # A removed clause must not pass the count check.
    ('clauses', 16, 'clauses'),
    ('clauses', 15.0, 'clauses'),
    ('returncode', 20, 'returncode 10'),
    ('returncode', 10.0, 'returncode 10'),
    ('sat', False, 'sat true'),
    ('sat', 1, 'sat true'),
    ('timed_out', True, 'timed_out false'),
    ('timed_out', 0, 'timed_out false'),
])
def test_individual_record_corruptions_are_rejected(field, value, reason):
    rec = record()
    rec[field] = value
    assert any(reason in problem for problem in record_problems('3-3-3_n3.json', rec))


def test_wrong_filename_is_rejected_independently_of_encoding():
    problems = record_problems('3-3-3_n4.json', record())
    assert len(problems) == 1 and 'file name' in problems[0]


@pytest.mark.parametrize('field', ['colouring', 'returncode', 'sat', 'timed_out',
                                   'problem', 'encoding', 'vars', 'clauses'])
def test_missing_required_sat_field_is_rejected(field):
    rec = record()
    del rec[field]
    assert record_problems('3-3-3_n3.json', rec)


@pytest.mark.parametrize(('field', 'value'), [
    ('returncode', 20), ('timed_out', False), ('timed_out', 1),
    ('sat', False), ('colouring', '001'),
])
def test_timeout_rejects_answer_or_inconsistent_status(field, value):
    rec = record(timeout=True)
    rec[field] = value
    assert record_problems('3-3-3_n3.json', rec)


@pytest.mark.parametrize('verdict', ['UNSAT', 'SOLVER_FAILED', '', None])
def test_uncertified_verdict_is_rejected(verdict):
    rec = record(timeout=True)
    rec['verdict'] = verdict
    assert any('not one this gate can re-check' in problem
               for problem in record_problems('3-3-3_n3.json', rec))


@pytest.mark.parametrize(('value', 'expected', 'answer'), [
    (1, 1, True), (True, 1, False), (1.0, 1, False), (False, 0, False),
    (True, True, True), (1, 2, False), (None, None, True),
])
def test_json_types_are_part_of_record_equality(value, expected, answer):
    assert same(value, expected) is answer
