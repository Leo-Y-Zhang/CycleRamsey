"""Enumerate the cycles of a complete graph, once each.

A cycle on an L-subset S is a cyclic sequence of all of S. Rotations and
reflections describe the same cycle, so each L-subset carries (L-1)!/2 of
them: 1 for a triangle, 60 for a 6-cycle.

This module is used by the ENCODER only. `verify_witness.py` deliberately
finds cycles by its own path search and imports nothing from here, so a bug
in this enumeration cannot hide inside the check that is supposed to catch it.
"""
from itertools import combinations, permutations


def cycles(n, length):
    """Yield every `length`-cycle of K_n exactly once, as a vertex tuple.

    The smallest vertex of the subset is pinned first, which removes the
    rotations; keeping only the orientations whose second vertex is smaller
    than the last removes the reflections.
    """
    if length < 3 or length > n:
        return
    for subset in combinations(range(n), length):
        head, rest = subset[0], subset[1:]
        for tail in permutations(rest):
            if tail[0] < tail[-1]:
                yield (head, *tail)


def cycle_count(n, length):
    """How many cycles `cycles(n, length)` yields, computed independently.

    The gate compares this against the enumeration; a formula that agrees
    with a generator it did not come from is worth more than either alone.
    """
    if length < 3 or length > n:
        return 0
    from math import comb, factorial
    return comb(n, length) * factorial(length - 1) // 2


def cycle_edges(cycle):
    """The edges of a cycle, each as a sorted pair, including the wrap-around."""
    return [tuple(sorted((cycle[i], cycle[(i + 1) % len(cycle)])))
            for i in range(len(cycle))]


def edges(n):
    """Every edge of K_n as a sorted pair, in a fixed order."""
    return list(combinations(range(n), 2))
