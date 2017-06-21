"""
Check normalization of a path on a hyperbolic tile grid.
"""

import json
import os.path
import re
from collections import namedtuple
from functools import partial

import numpy
from numpy import pi as π

def R(φ):
    φ2 = φ/2
    c = numpy.cos(φ2)
    s = numpy.sin(φ2)
    return numpy.array([[c, s], [-s, c]])

def T(d):
    d2 = d/2
    c = numpy.cosh(d2)
    s = numpy.sinh(d2)
    return numpy.array([[c, s], [s, c]])


class TilingKey(namedtuple("TilingKey", "p q")):
    unit_matrix = numpy.eye(2)

    def d(self, p, q):
        return 2*numpy.arccosh(numpy.cos(π/q) / numpy.sin(π/p))

    def φ(self, p):
        return 2*π/p

    def matrices(self):
        m_a = R(π) @ T(self.d(self.p, self.q))
        φ = self.φ(self.p)
        m_b = R(φ)
        m_B = R(-φ)
        return {"a": m_a, "A": m_a, "b": m_b, "B": m_B}

    def dual_matrices(self):
        d = self.d(self.q, self.p)
        Td = T(d)
        md_a = R(π) @ Td
        φ = self.φ(self.q)
        md_b = R(π+2*π/self.q) @ Td
        md_B = T(-d) @ R(π-2*π/self.q) 
        return {"a": md_a, "A": md_a, "b": md_b, "B": md_B}

    def matrix_of_path(self, path, dual=False):
        matrices = self.dual_matrices() if dual else self.matrices()
        result = self.unit_matrix
        for step in path:
            result = matrices[step] @ result
        return result

class RewritingSystem(object):
    @staticmethod
    def load_rules(filename):
        with open(filename, "r") as json_file:
            all_rules = json.load(json_file)
        result = {}
        for ruleset in all_rules.values():
            key = TilingKey(ruleset["p"], ruleset["q"])
            result[key] = RewritingSystem(key, ruleset["rules"])
        return result

    def __init__(self, key, rules):
        self.key = key
        self.rules = rules
        regex = "|".join("(" + re.escape(rule[0]) + ")" for rule in rules)
        self.regex = regex = re.compile(regex)
        self.replacements = replacements = (None,) + tuple(rule[1] for rule in rules)
        self._replace = partial(regex.subn, lambda mo: replacements[mo.lastindex])

    def normalize(self, expr):
        replace = self._replace
        go_on = True
        while go_on:
            expr, go_on = replace(expr)
        return expr

rules = RewritingSystem.load_rules(os.path.join(os.path.dirname(__file__), "hyperbolic.json"))

usage = """Normalize path on hyperbolic tile grid
Usage: {} p q [path]
p    - number of edges of each tile
q    - number of edges which come together in each corner
path - string containing of a, b, A, B, with:
        a,A - move one tile forward, then turn 180°
        b   - rotate one tile to the left
        B   - rotate one tile to the right
       If "path" is not given, a random path is generated.
"""

explanation = """Note:
The original and the normalized path should have (approximately)
the same matrix and dual matrix if normalization is correct, although they may
differ to a factor -1, i.e. one is the negative of the other."""

def matrix_diff(m1, m2):
    return numpy.abs(m1-m2).max()

def matrix_error(m1, m2):
    return min(matrix_diff(m1, m2), matrix_diff(m1, -m2))

def main():
    import sys
    import random
    if len(sys.argv) == 4:
        p, q, path = sys.argv[1:]
    elif len(sys.argv) == 3:
        p, q = sys.argv[1:]
        path = "a".join("".join(random.choice("bB") for j in range(random.randrange(1, int(p)))) for i in range(30))
    else:
        sys.stderr.write(usage.format(sys.argv[0]))
        sys.exit(1)
    p = int(p); q = int(q)
    key = TilingKey(p, q)
    try:
        ruleset = rules[key]
    except KeyError:
        sys.stderr.write("No rules available for p={}, q={}\n".format(p, q))
        sys.stderr.write("Available rules:\n")
        for p, q in sorted(rules.keys()):
            sys.stderr.write("p={}, q={}\n".format(p, q))
        sys.exit(1)
    m1 = key.matrix_of_path(path)
    md1 = key.matrix_of_path(path, dual=True)
    print("Original path: {}\nmatrix:\n{}\ndual matrix:\n{}".format(path, m1, md1))
    path2 = ruleset.normalize(path)
    m2 = key.matrix_of_path(path2)
    md2 = key.matrix_of_path(path2, dual=True)
    print("Normalized path: {}\nmatrix:\n{}\ndual matrix:\n{}".format(path2, m2, md2))
    print("Error: {}".format(matrix_error(m1, m2)))
    print("Dual error: {}".format(matrix_error(md1, md2)))
    print(explanation)



if __name__ == "__main__":
    main()
