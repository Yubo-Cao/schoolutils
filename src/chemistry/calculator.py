import json
from collections import namedtuple
from fractions import Fraction
from itertools import chain, groupby, starmap
from math import factorial, log, log10, sqrt
from operator import itemgetter
from pathlib import Path
from typing import List, Mapping, Set, Tuple

#: Barnett, M. (2021, 11). Alternative Regular Expression Module [Python Package].
#: from https://github.com/mrabarnett/mrab-regex.
from regex import MULTILINE, V1, Pattern, compile, escape, split, X

#: Atom type. An atom is any object where the string that has been used
# to parse and create it matches ATOM.
Atom = namedtuple("Atom", "name,value")

#: Supported operators.
FUNCTIONS: Set[str] = {"sqrt", "log10", "ln", "log", "fact"}
OPERATORS: Tuple[Set[str], ...] = (FUNCTIONS, {"**"}, {"*", "//", "/", "%"}, {"+", "-"})

#: Load datafile of period table. GoodmanScienses. (2022, 5). Periodic Table of
#: Elements.csv. from https://gist.github.com/GoodmanSciences/c2dd862cd38f21b0ad36b8f96b4bf1ee
try:
    with open(Path(__file__).resolve().parent / "periodic_table.json") as data:
        ATOMIC_MASS: Mapping[str, str] = json.loads(data.read())
except IOError as e:
    print(f"{e!r}")

#: Match an element in periodic table provided by "atomic_mass.json"
ELEMENT: str = "|".join(
    starmap(
        lambda a, b: (
            (
                f"{a}[{''.join(set(map(lambda e: e[1:], b)))}]{'?' if any(map(lambda e: len(e) == 1, b)) else ''}"
            )
            if any(map(lambda e: len(e) > 1, b))
            else a
        )
        if len(b := set(b)) > 0
        else "",
        groupby(sorted(ATOMIC_MASS.keys()), key=itemgetter(0)),
    )
)

#: Match an operator, identifier(which is considered operator this case).
OPERATOR: str = "|".join(map(escape, sorted(chain(*OPERATORS), key=len, reverse=True)))

#: Match a bracket in BRACKETS.
BRACKET: str = "\\(|\\)"

#: Match a number. May optionally be floating point, in scientific notation, or haveing
#: preceding +/- sign.
NUMBER: str = f"(?:(?<=(?:{OPERATOR}|{BRACKET})\s*)[+-]|^[+-]|)((?:\d*\.\d+|\d+\.?\d*)(?:[eE][+-]?\d+)?)"

#: Match a compound, e.g/,  H_{2}O. Curly braces and underscore are optional.
COMPOUND_ATOM: str = f"""(?P<element>{ELEMENT})(?|_{{(?P<subscript>\d+)}}|_(?P<subscript>\d+)|(?P<subscript>\d*))|(?P<element>(?<={ELEMENT}|\d|}})\))(?|_{{(?P<subscript>\d+)}}|_(?P<subscript>\d+)|(?P<subscript>\d+))|(?<!(?:{OPERATOR})\s*)(?P<element>\()(?={ELEMENT})"""
COMPOUND_ATOM_RE: Pattern = compile(COMPOUND_ATOM, MULTILINE | V1 | X)
FORMULA: str = f"(?:{COMPOUND_ATOM})+"

#: Any above items may optionally enclosed between paired brackets -- enclosure.
#: Match a enclosure.
ENCLOSURE: str = f"(?P<enclosure>\((?:((?:({ELEMENT})(?|_{{(\d+)}}|_(\d+)|(\d*))|((?<={ELEMENT}|\d|}})\))(?|_{{(\d+)}}|_(\d+)|(\d+))|(?<!(?:{OPERATOR})\s*)(\()(?={ELEMENT}))+|{NUMBER}|{OPERATOR}|\s)+|(?&enclosure))*\))"

#: Atom is the baic component of expression. Atoms form expression.
ATOM: str = (
    f"{ENCLOSURE}|(?P<formula>{FORMULA})|(?P<number>{NUMBER})|(?P<operator>{OPERATOR})"
)
ATOM_RE: Pattern = compile(ATOM, MULTILINE | V1 | X)

print(ATOM)

def atomize(to_be_parse: str) -> List[Atom]:
    """
    Parse user input into a list of atoms.
    """
    atom_list: List[Atom] = [
        Atom(match.lastgroup, match.group(0)) for match in ATOM_RE.finditer(to_be_parse)
    ]

    if "".join(map(lambda atom: atom.value, atom_list)) != "".join(
            split(r"\s+", to_be_parse)
    ):
        raise ValueError("Illegal expression.")
    if len(atom_list) == 0:
        raise ValueError("Empty expression.")
    return atom_list


def evaluate(exp: List[Atom]) -> Fraction:
    #: Shallow copy of expression, so that original expression is not modified.
    result: List[Fraction | Atom] = exp.copy()
    #: Iterate over precedence, from highest to lowest so that BODMAS is ensured.
    for precedence in OPERATORS:
        index: int = 0
        #: Iterate over result. Backtrack and evaluate it again, whenever necessary.
        while index < len(result):
            atom = result[index]
            name, value = atom
            #: If it is a operator, and at correct precedence.
            if name == "operator" and value in precedence:
                if (
                        value in FUNCTIONS
                        and index < len(exp) - 1
                        and (a := result[index + 1]).name == "number"
                ):
                    identifier, argument = value, Fraction(a.value)
                    result[index: index + 2] = [
                        Atom("number", __evaluate_function(identifier, argument))
                    ]
                elif (
                        0 < index < len(exp) - 1
                        and (a := result[index - 1]).name == "number"
                        and (b := result[index + 1]).name == "number"
                ):
                    first_operand, infix_operator, second_operand = (
                        Fraction(a.value),
                        value,
                        Fraction(b.value),
                    )
                    result[index - 1: index + 2] = [
                        Atom(
                            "number",
                            __evaluate_infix_operator(
                                first_operand, infix_operator, second_operand
                            ),
                        )
                    ]
                    index -= 1
            #: If is a chemical formula.
            elif name == "formula":
                result[index] = Atom("number", __evaluate_formula_mass(atom))
                index = max(index - 3, -1)
            #: If has brackets around.
            elif name == "enclosure":
                result[index] = Atom(
                    "number", evaluate(atomize(value[1:-1]))
                )  # If it is a bracket, then evaluate the inner expression as results
                index = max(index - 3, -1)
            index += 1
    if len(result) != 1:
        raise ValueError("Illegal expression.")
    return result[0].value


def __evaluate_infix_operator(
        first_operand: Fraction, infix_operator: str, second_operand: Fraction
) -> Fraction:
    """
    It takes two operands and an infix operator, and returns the result of applying the
    infix operator to the two operands.
    """
    if infix_operator == "**":
        return first_operand ** second_operand
    elif infix_operator == "+":
        return first_operand + second_operand
    elif infix_operator == "-":
        return first_operand - second_operand
    elif infix_operator == "*":
        return first_operand * second_operand
    elif infix_operator == "/":
        return first_operand / second_operand
    elif infix_operator == "//":
        return first_operand // second_operand
    elif infix_operator == "%":
        return first_operand % second_operand


def __evaluate_function(identifier: str, arguments: Fraction) -> Fraction:
    """
    It takes in a function identifier and an argument, and returns the result of the
    function.
    """
    if identifier == "sqrt":
        return Fraction(sqrt(arguments))
    elif identifier == "log10" or identifier == "log":
        return Fraction(log10(arguments))
    elif identifier == "ln":
        return Fraction(log(arguments))
    elif identifier == "fact":
        return Fraction(factorial(arguments))
    else:
        raise ValueError(f"Supported function: {identifier}")


def __evaluate_formula_mass(atom: Atom) -> Fraction:
    """
    Given a formula typed atom representing a chemical formula, return the molecular
    weight of the corresponding molecule.
    """

    stack: List[Fraction] = [Fraction(0.0)]
    for match in COMPOUND_ATOM_RE.finditer(atom.value):
        group = match.group("element")
        if group == "(":
            stack.append(Fraction(0))
        elif group == ")":
            top = stack.pop()
            subscript = Fraction(match.group("subscript"))
            stack[-1] = stack[-1] + top * subscript
        else:
            element = group
            stack[-1] = stack[-1] + Fraction(ATOMIC_MASS[element]) * Fraction(
                match.group("subscript") if match.group("subscript") else Fraction(1)
            )
    return stack.pop()


#: If user input in SENTINEL, exit the calculator.
SENTINEL: Set[str] = {"quit", "exit"}

GREETING: str = f"""
Calculator that support {", ".join(chain(*OPERATORS))}.
For any formula input into this calculator, the formula mass is automatically calculated.
Input any expression after >>>
And the results of evaluation is printed to stdout with ⟹
""".strip()


def main() -> None:
    """
    The main function of this module is to take an expression as input
    and print the result of that expression. The main function also takes
    care of any errors that may occur during the evaluation process.
    """

    print(GREETING)

    while True:
        try:
            exp = input(">>> ")
            if exp.lower() in SENTINEL:
                break
            if exp.startswith("#"):
                continue
            atom_list = atomize(exp)
            final_result = evaluate(atom_list)
            try:
                print(f"⟹ {final_result!s} ≈ {float(final_result)!s}")
            except OverflowError as e:
                print(f"⟹ {final_result!s}")
        except (EOFError, KeyboardInterrupt):
            break
        except IndexError:
            print(f"\033[91mThere is an error in your expression.\033[0m")
        except Exception as e:
            print(f"\033[91m{e!r}\033[0m")


if __name__ == "__main__":
    main()
