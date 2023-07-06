import argparse
from io import TextIOWrapper
from typing import List, Optional

class Literal:
    index = 0
    def __init__(self, str, positive) -> None:
        self.str = str
        self.positive = positive
        self.index += 1
    def __invert__(self):
        return Literal(self.str, not self.positive)
    def __add__(self, other):
        if isinstance(other, TrueLiteral):
            return TrueLiteral
        if (isinstance(other, bool)):
            return TrueLiteral if other else self
        if (isinstance(other, Literal)):
            if (other.str == self.str):
                if other.positive != self.positive:
                    return TrueLiteral
                return self
        return Clause([self, other])
    def __hash__(self) -> int:
        return hash(self.str)
    def __eq__(self, o: object) -> bool:
        return isinstance(o, Literal) and o.str == self.str and o.positive == self.positive

class Clause:
    count = 0
    def __init__(self, literals: List[Literal], parentOne: Optional['Clause'] = None, parentTwo: Optional['Clause'] = None) -> None:
        self.literals = set(literals)
        self.parentOne = parentOne
        self.parentTwo = parentTwo
        self.index = type(self).count + 1
        type(self).count += 1
    def __hash__(self) -> int:
        return 0
    def __eq__(self, o: object) -> bool:
        return isinstance(o, Clause) and self.literals == o.literals
    def __str__(self) -> str:
        str = ""
        for literal in self.literals:
            if literal.positive:
                str += literal.str + " v "
            else:
                str += "~" + literal.str + " v " 
        str = str.strip(" v ")
        return str
    def __contains__(self, other):
        if isinstance(other, Literal):
            return other in self.literals
        if isinstance(other, Clause):
            return self.literals.issuperset(other.literals)
        return False
    def __add__(self, other):
        if isinstance(other, bool):
            if other == True:
                return TrueClause
            return self
        if isinstance(other, Literal):
            if isinstance(other, TrueLiteral):
                return TrueClause
            if other in self.literals:
                return self
            if not other in self.literals:
                return TrueClause()
        if isinstance(other, Clause):
            if isinstance(other, TrueClause):
                return TrueClause
            if other in self:
                return self
            if self in other:
                return other
            return Clause(other.literals.union(self.literals))
    def __invert__(self) -> List['Clause']:
        negated = []
        for literal in self.literals:
            negated.append(Clause([~literal]))
        return negated
    def check_tauntology(self): 
        for literal in self.literals:
            if ~literal in self.literals:
                return True
        return False
    def resolve_with(self, clause: 'Clause'):
        for literal in self.literals:
            if ~literal in clause:
                if len(self.literals) == 1 and len(clause.literals) == 1:
                    return NilClause(self, clause)
                
                new_clause = self + clause
                new_clause.parentOne = self
                new_clause.parentTwo = clause
                new_clause.literals.remove(literal)
                new_clause.literals.remove(~literal)
                if new_clause.check_tauntology():
                    return None
                return new_clause
    

class TrueLiteral(Literal):
    def __init__(self) -> None:
        super().__init__("TRUE", True)

class TrueClause(Clause):
    def __init__(self) -> None:
        super().__init__([TrueLiteral()])

class NilLiteral(Literal):
    def __init__(self) -> None:
        super().__init__("NIL", True)

class NilClause(Clause):
    def __init__(self, parentOne: Optional[Clause] = None, parentTwo: Optional[Clause] = None) -> None:
        super().__init__([NilLiteral()], parentOne, parentTwo)

def keep_smaller(clauses: List[Clause], new_clauses):
    index = len(clauses)
    for new_clause in new_clauses:
        clauses_temp = clauses
        keep = True
        for clause in clauses:
            if new_clause in clause:
                clauses_temp.remove(clause)
                index -= 1
            elif clause in new_clause:
                keep = False
                break
        clauses = clauses_temp
        if keep:
            clauses.append(new_clause)
    return clauses, index

def resolve(clauses: List[Clause], index: int):
    while index != len(clauses):
        new_clauses = set()
        for i in range(index, len(clauses)):
            for clause in clauses:
                resolved = clauses[i].resolve_with(clause)
                if isinstance(resolved, NilClause):
                    return resolved
                if resolved != None:
                    new_clauses.add(resolved)
        clauses, index = keep_smaller(clauses, new_clauses)
    return False

def line_to_clause(line: str) -> Clause:
    line = line.lower()
    return Clause((Literal(c.strip(" ~"), not c.strip().startswith("~")) for c in line.split(" v ")))

def prove_clause(clause: Clause, clauses: List[Clause]):
    index = len(clauses)
    for c in (~clause):
        clauses.append(c)
    print_clauses(clauses)
    resolved = resolve(clauses, index)
    if resolved != False:
        print_all(resolved)
        print("[CONCLUSION]: " + str(clause) + " is true")
    else:
        print("[CONCLUSION]: " + str(clause) + " is unknown")

def resolve_action(clauses: List[Clause], filename: str):
    with open(filename) as file:
        lines = file.readlines()
    for line in lines:
        print("Users command:" + line.strip())
        if line[0] == '#':
            continue
        if line[-2] == '+':
            clauses.append(line_to_clause(line.strip(' +\n')))
            print("Added " + line.strip(' +\n'))
        if line[-2] == '-':
            clauses.remove(line_to_clause(line.strip(' -\n')))
            print("Removed " + line.strip(' -\n'))
        if line[-2] == '?':
            clause_prove = line_to_clause(line.strip(' ?\n'))
            temp_clauses = list(clauses)
            prove_clause(clause_prove, temp_clauses)
        print()


def load_next_line(file: TextIOWrapper):
    line = file.readline().strip()
    if len(line) == 0:
        return 0
    if line[0] != "#":
        return line
    return load_next_line(file)

def load_clauses(filename: str):
    clauses = list()
    with open(filename) as file:
        line = load_next_line(file)
        line = line.lower()
        last_clause = line_to_clause(line)
        line = load_next_line(file)
        while line:
            if not last_clause.check_tauntology():
                clauses.append(last_clause)
            last_clause = line_to_clause(line)
            line = load_next_line(file)
    return clauses, last_clause

def print_all(clause: Clause):
    if clause.parentOne and clause.parentTwo:
        print_all(clause.parentOne)
        print_all(clause.parentTwo)
        print(str(clause.index) + ": " + str(clause) + "(" + str(clause.parentOne.index) + ", " + str(clause.parentTwo.index) + ")")

def print_clauses(clauses: List[Clause]):
    for c in clauses:
        print(str(c.index) + ": " + str(c))
    print("=================")

parser = argparse.ArgumentParser()
parser.add_argument('action')
parser.add_argument('clauses_filename')
parser.add_argument('input_filename', nargs='?', default="")
args = parser.parse_args()
clauses_filename = args.clauses_filename
clauses, last_clause = load_clauses(clauses_filename)

if args.action == 'resolution':
    prove_clause(last_clause, clauses)

if args.action == 'cooking':
    clauses.append(last_clause)
    input_filename = args.input_filename
    resolve_action(clauses, input_filename)