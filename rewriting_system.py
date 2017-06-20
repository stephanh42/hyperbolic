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

    def d(self):
        return 2*numpy.arccosh(numpy.cos(π/self.q) / numpy.sin(π/self.p))

    def φ(self):
        return 2*π/self.p

    def matrices(self):
        m_a = R(π) @ T(self.d())
        φ = self.φ()
        m_b = R(φ)
        m_B = R(-φ)
        return {ord("a"): m_a, ord("A"): m_a, ord("b"): m_b, ord("B"): m_B}

    def matrix_of_path(self, path):
        matrices = self.matrices()
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
        regex = b"|".join(b"(" + re.escape(rule[0].encode("ASCII")) + b")" for rule in rules)
        self.regex = regex = re.compile(regex)
        self.replacements = replacements = (None,) + tuple(rule[1].encode("ASCII") for rule in rules)
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
the same matrix if normalization is correct, although they may
differ to a factor -1, i.e. one is the negative of the other."""

def matrix_diff(m1, m2):
    return numpy.abs(m1-m2).max()

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
    bpath = path.encode("ASCII")
    m1 = key.matrix_of_path(bpath)
    print("Original path: {}\nmatrix:\n{}".format(path, m1))
    bpath2 = ruleset.normalize(bpath)
    path2 = bpath2.decode("ASCII")
    m2 = key.matrix_of_path(bpath2)
    print("Normalized path: {}\nmatrix:\n{}".format(path2, m2))
    err = min(matrix_diff(m1, m2), matrix_diff(m1, -m2))
    print("Error: {}".format(err))
    print(explanation)



if __name__ == "__main__":
    main()
