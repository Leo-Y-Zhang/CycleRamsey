from itertools import combinations, permutations, product

import pytest

from ramsey.encode import Encoding


def satisfies(clauses, true_vars):
    return all(any((lit in true_vars) if lit > 0 else (-lit not in true_vars)
                   for lit in clause) for clause in clauses)


def test_variable_numbers_are_contiguous_one_based():
    enc = Encoding(3, (3, 3, 3))
    assert enc.edges == [(0, 1), (0, 2), (1, 2)]
    assert [enc.var(edge, c) for edge in enc.edges for c in range(3)] == list(range(1, 10))
    assert enc.num_vars == 9


def test_one_hot_rejects_no_colour_and_each_multiple_assignment():
    enc = Encoding(2, (3, 3, 3))
    for bits in product((False, True), repeat=3):
        assert satisfies(enc.clauses, {i + 1 for i, bit in enumerate(bits) if bit}) == (
            sum(bits) == 1)


def test_cnf_matches_definition_for_every_k4_colouring():
    targets = (3, 4, 3)
    enc = Encoding(4, targets)
    pairs = list(combinations(range(4), 2))
    for colours in product(range(3), repeat=len(pairs)):
        colouring = dict(zip(pairs, colours, strict=True))
        good = not any(
            all(colouring[tuple(sorted((path[i - 1], path[i])))] == colour
                for i in range(length))
            for colour, length in enumerate(targets)
            for path in permutations(range(4), length))
        # Independent DIMACS numbering, so encoder map bugs cannot cancel out.
        true_vars = {3 * i + colour + 1 for i, colour in enumerate(colours)}
        assert satisfies(enc.clauses, true_vars) == good, colours


@pytest.mark.parametrize('colour', range(3))
def test_cycle_clause_has_every_edge_and_correct_colour(colour):
    targets = [6, 6, 6]
    targets[colour] = 5
    enc = Encoding(5, targets)
    ring = {(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)}
    expected = frozenset(-(3 * i + colour + 1)
                         for i, e in enumerate(enc.edges) if e in ring)
    assert expected in {frozenset(cl) for cl in enc.clauses}


@pytest.mark.parametrize('targets', [(), (3, 3), (3, 3, 3, 3), (2, 3, 3)])
def test_invalid_targets(targets):
    with pytest.raises(ValueError):
        Encoding(3, targets)


def test_decode_valid_signed_multiline_model():
    enc = Encoding(3, (3, 3, 3))
    assert enc.colouring_from_model([1, -2, -3, 4, -5, -6, -7, 8, -9, 0]) == {
        (0, 1): 0, (0, 2): 0, (1, 2): 1}


@pytest.mark.parametrize('model', [[1, 4], [1, 2, 4, 8], [-1, -4, -8], []])
def test_decode_refuses_truncated_or_multiple_colour_model(model):
    with pytest.raises(ValueError, match='colours, not one'):
        Encoding(3, (3, 3, 3)).colouring_from_model(model)


def test_dimacs_has_correct_header_clauses_and_terminators(tmp_path):
    enc = Encoding(3, (3, 3, 3))
    path = tmp_path / 'small.cnf'
    assert enc.to_dimacs(path) == path
    lines = path.read_text(encoding='ascii').splitlines()
    assert lines[0] == 'p cnf 9 15'
    assert len(lines[1:]) == 15
    clauses = []
    for line in lines[1:]:
        values = [int(token) for token in line.split()]
        assert values[-1] == 0
        assert all(1 <= abs(value) <= 9 for value in values[:-1])
        clauses.append(values[:-1])
    assert clauses == enc.clauses
    assert path.read_bytes().endswith(b' 0\n')
