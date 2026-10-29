from itertools import combinations, product

import pytest

from ramsey import symmetry
from ramsey.cycles import cycle_count, cycle_edges, cycles, edges
from ramsey.encode import Encoding


def test_cycle_edges_include_sorted_closing_edge():
    assert cycle_edges((3, 1, 0, 2)) == [(1, 3), (0, 1), (0, 2), (2, 3)]
    assert cycle_edges(()) == []


@pytest.mark.parametrize(('n', 'length', 'count'), [
    (2, 3, 0), (4, 2, 0), (3, 3, 1), (4, 3, 4), (4, 4, 3), (5, 4, 15),
])
def test_cycle_counts_and_unique_undirected_cycles(n, length, count):
    result = list(cycles(n, length))
    assert len(result) == cycle_count(n, length) == count
    assert len({frozenset(cycle_edges(c)) for c in result}) == count
    for cycle in result:
        assert len(set(cycle)) == length
        assert cycle[0] == min(cycle)
        assert cycle[1] < cycle[-1]


def test_edges_have_all_vertices_and_stable_order():
    assert edges(4) == [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    assert edges(0) == edges(1) == []


def test_symmetry_clauses_accept_exactly_sorted_stars():
    enc = Encoding(4, (5, 5, 5))
    clauses = symmetry.sorted_star_clauses(enc)
    assert len(clauses) == 6
    for colours in product(range(3), repeat=3):
        true_vars = {enc.var((0, i + 1), c) for i, c in enumerate(colours)}
        accepted = all(any(-lit not in true_vars if lit < 0 else lit in true_vars
                           for lit in clause) for clause in clauses)
        assert accepted == (list(colours) == sorted(colours)), colours


def test_apply_appends_only_the_break_and_returns_actual_count():
    enc = Encoding(4, (5, 5, 5))
    original = [list(clause) for clause in enc.clauses]
    expected = symmetry.sorted_star_clauses(enc)
    assert symmetry.apply(enc) == 6
    assert enc.clauses == original + expected


def test_canonicalise_preserves_all_edge_colours_under_vertex_permutation():
    colouring = dict(zip(combinations(range(4), 2), [2, 0, 1, 2, 1, 0], strict=True))
    # Old vertices 2, 3, 1 become 1, 2, 3, respectively.
    expected = {(0, 1): 0, (0, 2): 1, (0, 3): 2,
                (1, 2): 0, (1, 3): 2, (2, 3): 1}
    saved = dict(colouring)
    assert symmetry.canonicalise(4, colouring) == expected
    assert colouring == saved
    assert symmetry.canonicalise(4, expected) == expected
