"""CNF for: does K_n admit a 3-colouring with no monochromatic target cycle?

The question behind R(C_a, C_b, C_c) is whether the edges of K_n can be
coloured in three colours so that colour 0 contains no C_a, colour 1 no C_b
and colour 2 no C_c. That formula is satisfiable exactly when n < R, so

    R(C_a, C_b, C_c) = the least n at which it is unsatisfiable.

The encoding is the definition and nothing else. There is no symmetry
breaking here on purpose: a proof of a symmetry-broken formula does not prove
the original statement, and the refutations this repository certifies have to
be refutations of the real question.
"""
from .cycles import cycle_edges, cycles, edges

NUM_COLOURS = 3


class Encoding:
    """The CNF, plus the variable map a witness needs to be read back."""

    def __init__(self, n, targets):
        if len(targets) != NUM_COLOURS:
            raise ValueError('exactly three target cycle lengths are required')
        self.n = n
        self.targets = tuple(targets)
        self.edges = edges(n)
        self.edge_index = {e: i for i, e in enumerate(self.edges)}
        self.clauses = []
        self._build()

    # ---- variables -------------------------------------------------------
    # One-hot: var(e, c) is true when edge e has colour c. Variables are
    # numbered from 1 because DIMACS has no variable 0.

    def var(self, edge, colour):
        return NUM_COLOURS * self.edge_index[edge] + colour + 1

    @property
    def num_vars(self):
        return NUM_COLOURS * len(self.edges)

    # ---- clauses ---------------------------------------------------------

    def _build(self):
        # Every edge gets at least one colour, and at most one. Both halves
        # are needed: without at-least-one an "uncoloured" edge would satisfy
        # everything, and without at-most-one the assignment is not a
        # colouring, which is what the definition asks about.
        for e in self.edges:
            self.clauses.append([self.var(e, c) for c in range(NUM_COLOURS)])
            for c1 in range(NUM_COLOURS):
                for c2 in range(c1 + 1, NUM_COLOURS):
                    self.clauses.append([-self.var(e, c1), -self.var(e, c2)])

        # For each colour, forbid every cycle of that colour's target length:
        # at least one of its edges must miss that colour.
        for colour, length in enumerate(self.targets):
            for cyc in cycles(self.n, length):
                self.clauses.append(
                    [-self.var(e, colour) for e in cycle_edges(cyc)])

    # ---- output ----------------------------------------------------------

    def to_dimacs(self, path):
        with open(path, 'w', encoding='ascii', newline='\n') as fh:
            fh.write(f'p cnf {self.num_vars} {len(self.clauses)}\n')
            for cl in self.clauses:
                fh.write(' '.join(map(str, cl)))
                fh.write(' 0\n')
        return path

    def colouring_from_model(self, model):
        """Turn a DIMACS model into {edge: colour}, checking it is a colouring.

        Reads the assignment back through the same variable map that wrote it,
        and refuses anything that is not exactly one colour per edge - a
        malformed model must not be handed on as if it were a witness.
        """
        true_vars = {v for v in model if v > 0}
        colouring = {}
        for e in self.edges:
            assigned = [c for c in range(NUM_COLOURS)
                        if self.var(e, c) in true_vars]
            if len(assigned) != 1:
                raise ValueError(
                    f'model gives edge {e} {len(assigned)} colours, not one')
            colouring[e] = assigned[0]
        return colouring
