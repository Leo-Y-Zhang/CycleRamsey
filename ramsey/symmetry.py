"""Satisfiability-preserving symmetry breaking, and the argument for it.

Whether a colouring is good depends only on which cycles are monochromatic,
and a permutation of the vertices carries cycles to cycles of the same length
in the same colour. So the vertex group S_n acts on good colourings, and if
any good colouring exists then one exists in any canonical form we can define
by that action. Adding a constraint that every orbit meets is therefore
satisfiability-preserving: the broken formula is satisfiable exactly when the
raw one is, and an UNSAT of the broken formula is an UNSAT of the question.

That argument is only as good as its implementation, so `verify_all.py`
re-decides every known value both ways and requires the same verdict. A
symmetry break that quietly removed a real colouring would show up there as a
SAT that turned into an UNSAT.

Only one break is implemented, deliberately: the colours along the edges
leaving vertex 0 are non-decreasing. Vertices 1..n-1 may be permuted freely,
so every good colouring has a representative in this form.
"""


def sorted_star_clauses(enc):
    """Force colour(0,1) <= colour(0,2) <= ... <= colour(0,n-1).

    With one-hot variables the comparison is three forbidden pairs per
    consecutive edge: a later edge may not carry a strictly smaller colour.
    """
    clauses = []
    star = [(0, v) for v in range(1, enc.n)]
    for a, b in zip(star, star[1:]):
        for hi in range(1, 3):
            for lo in range(hi):
                clauses.append([-enc.var(a, hi), -enc.var(b, lo)])
    return clauses


def apply(enc):
    """Append the break to an encoding, in place. Returns how many clauses."""
    extra = sorted_star_clauses(enc)
    enc.clauses.extend(extra)
    return len(extra)


def canonicalise(n, colouring):
    """Permute vertices 1..n-1 so the star at vertex 0 is sorted by colour.

    Used by the tests: any good colouring must survive this and stay good,
    which is the concrete form of the argument above.
    """
    order = sorted(range(1, n), key=lambda v: colouring[tuple(sorted((0, v)))])
    mapping = {0: 0}
    for new, old in enumerate(order, start=1):
        mapping[old] = new
    out = {}
    for (u, w), c in colouring.items():
        a, b = mapping[u], mapping[w]
        out[tuple(sorted((a, b)))] = c
    return out
