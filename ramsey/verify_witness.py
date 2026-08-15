"""Solver-free check of a claimed good colouring.

This reads the definition, not the CNF, and it finds cycles by its own
depth-first path search rather than by importing the encoder's enumeration.
That is the whole point: if `cycles.py` missed some cycle, the encoder would
build a formula that is too easy and the solver would hand back a colouring
that is not actually good. Only a checker that shares no code with the
encoder can catch that.

A colouring is `good` for (a, b, c) on K_n when colour 0 contains no cycle of
length exactly a, colour 1 none of length b, and colour 2 none of length c.
"""


def adjacency(n, colouring, colour):
    """Neighbour sets of the subgraph in one colour."""
    adj = {v: set() for v in range(n)}
    for (u, w), c in colouring.items():
        if c == colour:
            adj[u].add(w)
            adj[w].add(u)
    return adj


def find_cycle(n, colouring, colour, length):
    """Return a cycle of exactly `length` in this colour, or None.

    Every cycle is found from its smallest vertex, so the search only ever
    walks to vertices above the start. That makes each cycle reachable by
    exactly one root and keeps the walk finite without a visited-set trick
    that could accidentally prune a real cycle.
    """
    if length < 3 or length > n:
        return None
    adj = adjacency(n, colouring, colour)

    def walk(start, path, seen):
        if len(path) == length:
            return list(path) if start in adj[path[-1]] else None
        for nxt in adj[path[-1]]:
            if nxt <= start or nxt in seen:
                continue
            path.append(nxt)
            seen.add(nxt)
            found = walk(start, path, seen)
            if found is not None:
                return found
            seen.discard(nxt)
            path.pop()
        return None

    for start in range(n):
        found = walk(start, [start], {start})
        if found is not None:
            return found
    return None


def check_colouring(n, colouring, targets):
    """Raise unless `colouring` is a complete, proper, good colouring of K_n."""
    expected = n * (n - 1) // 2
    if len(colouring) != expected:
        raise AssertionError(
            f'colouring has {len(colouring)} edges, K_{n} has {expected}')
    for u in range(n):
        for w in range(u + 1, n):
            if (u, w) not in colouring:
                raise AssertionError(f'edge {(u, w)} is uncoloured')
            if colouring[(u, w)] not in (0, 1, 2):
                raise AssertionError(f'edge {(u, w)} has a colour outside 0..2')
    for colour, length in enumerate(targets):
        found = find_cycle(n, colouring, colour, length)
        if found is not None:
            raise AssertionError(
                f'colour {colour} contains the {length}-cycle {found}')
    return True


def is_good(n, colouring, targets):
    try:
        return check_colouring(n, colouring, targets)
    except AssertionError:
        return False
