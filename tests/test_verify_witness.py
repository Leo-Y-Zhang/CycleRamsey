from itertools import combinations, permutations

import pytest

from ramsey.verify_witness import adjacency, check_colouring, find_cycle, is_good


@pytest.mark.parametrize('colour', range(3))
def test_valid_witness_and_one_changed_colour(colour):
    good = {(0, 1): colour, (0, 2): colour, (1, 2): (colour + 1) % 3}
    assert check_colouring(3, good, (3, 3, 3)) is True
    assert is_good(3, good, (3, 3, 3)) is True
    bad = dict(good)
    bad[(1, 2)] = colour
    with pytest.raises(AssertionError, match='contains the 3-cycle'):
        check_colouring(3, bad, (3, 3, 3))
    assert is_good(3, bad, (3, 3, 3)) is False


@pytest.mark.parametrize('corruption', ['missing', 'extra', 'reversed', 'wrong-key'])
def test_incomplete_or_malformed_edge_set(corruption):
    colouring = {(0, 1): 0, (0, 2): 0, (1, 2): 1}
    if corruption == 'missing':
        del colouring[(1, 2)]
    elif corruption == 'extra':
        colouring[(0, 3)] = 2
    else:
        del colouring[(1, 2)]
        colouring[(2, 1) if corruption == 'reversed' else (0, 3)] = 1
    with pytest.raises(AssertionError):
        check_colouring(3, colouring, (3, 3, 3))
    assert is_good(3, colouring, (3, 3, 3)) is False


@pytest.mark.parametrize('value', [-1, 3, '0', None])
def test_invalid_colour(value):
    colouring = {(0, 1): value, (0, 2): 0, (1, 2): 1}
    with pytest.raises(AssertionError, match=r'outside 0\.\.2'):
        check_colouring(3, colouring, (3, 3, 3))
    assert is_good(3, colouring, (3, 3, 3)) is False


@pytest.mark.parametrize('targets', [(2, 3, 3), (3, 0, 3), (3, 3, -1)])
def test_invalid_question_propagates_through_is_good(targets):
    with pytest.raises(ValueError, match='at least 3'):
        is_good(3, {(0, 1): 0, (0, 2): 0, (1, 2): 1}, targets)


def test_adjacency_is_undirected_and_colour_specific():
    colouring = {(0, 2): 1, (1, 2): 0, (0, 1): 2}
    assert adjacency(4, colouring, 1) == {0: {2}, 1: set(), 2: {0}, 3: set()}


def test_cycle_search_against_small_graphs():
    # Exhaust all 64 subgraphs of K4. This oracle lists vertex sequences,
    # independently of the checker's DFS and the encoder's cycle generator.
    pairs = list(combinations(range(4), 2))
    for mask in range(1 << len(pairs)):
        graph = {edge: 0 for bit, edge in enumerate(pairs) if mask & (1 << bit)}
        for length in (3, 4):
            expected = any(
                all(tuple(sorted((path[i - 1], path[i]))) in graph for i in range(length))
                for path in permutations(range(4), length))
            found = find_cycle(4, graph, 0, length)
            assert (found is not None) == expected, (mask, length)
            if found is not None:
                assert len(found) == len(set(found)) == length
                assert all(tuple(sorted((found[i - 1], found[i]))) in graph
                           for i in range(length))
    assert find_cycle(4, {}, 0, 2) is None
    assert find_cycle(4, {}, 0, 5) is None


def test_cycle_can_start_above_zero_and_requires_backtracking():
    graph = {(0, 1): 0, (1, 2): 0, (2, 3): 0, (3, 4): 0, (1, 4): 0}
    found = find_cycle(5, graph, 0, 4)
    assert found is not None and set(found) == {1, 2, 3, 4}
    assert find_cycle(5, graph, 0, 3) is None
