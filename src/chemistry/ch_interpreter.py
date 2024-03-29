from contextlib import contextmanager
from decimal import Decimal
from functools import singledispatchmethod
from typing import Any, NoReturn

from ch_ast import (
    Assign,
    Binary,
    During,
    Grouping,
    Literal,
    Unary,
    Variable,
    Conversion,
    Exam,
    Redo,
    Interval,
    ExprStmt,
    Work,
    Submit,
    Call,
    Block,
    Write,
)
from ch_env import Env
from ch_error import CHError
from ch_handler import handler
from ch_objs import CHQuantity, CHString, Formula, FormulaUnit
from ch_token import *
from ch_work import CHWork, SubmitError, NativeWork


class Interpreter:
    _singleton = None

    def __new__(cls: type) -> "Interpreter":
        # Hack: make sure the interpreter is singleton
        if Interpreter._singleton is None:
            Interpreter._singleton = super().__new__(cls)
        return Interpreter._singleton

    def __init__(self):
        if not getattr(self, "inited", False):
            self.global_env = Interpreter.init_global_env()
            self.env = self.global_env
        self.inited = True

    @contextmanager
    def scope(self, env=None):
        prev = self.env
        self.env = Env(self.env) if env is None else env
        yield
        self.env = prev

    @staticmethod
    def init_global_env():
        env = (
            Env()
            .assign("attribute_to_evaluate_element", "AtomicMass")
            .assign("show_balanced_equation", True)
            .assign("print", NativeWork(lambda x: print(Interpreter.stringify(x)), 1))
            .assign("input", NativeWork(input, 1))
        )
        import math, inspect

        for name, f in [
            member
            for member in inspect.getmembers(math)
            if callable(member[1]) and not member[0].startswith("__")
        ]:

            def _deco(func):
                def _wrapper(arg):
                    if isinstance(arg, CHQuantity):
                        arg = arg.value
                    return func(arg)

                return _wrapper

            env = env.assign(name, NativeWork(_deco(f), 1))
        return env

    def interpret(self, node: Any) -> Any:
        return Interpreter.stringify(self.evaluate(node))

    def execute(self, node: Any) -> Any:
        """
        Execute a list of statements.
        """

        res = None
        if isinstance(node, Block):
            for stmt in node.body:
                res = self.evaluate(stmt)
        elif isinstance(node, list):
            for stmt in node:
                res = self.evaluate(stmt)
        else:
            res = self.evaluate(node)
        return res

    @staticmethod
    def stringify(val: Any) -> str:
        if val is None:
            return "na"
        elif val is True:
            return "pass"
        elif val is False:
            return "fail"
        else:
            return str(val)

    @singledispatchmethod
    def evaluate(self, node: Any) -> Any:
        pass

    @evaluate.register(Write)
    def _eval_write(self, node: Write) -> Any:
        try:
            with open(node.path, "a+") as f:
                f.write(self.stringify(val := self.evaluate(node.expr)))
            return val
        except IOError:
            raise handler.error("Could not open file %s " % node.path, node.to.line)

    @evaluate.register(During)
    def _eval_during(self, node: During) -> Any:
        while self.evaluate(node.cond):
            self.execute(node.body)

    @evaluate.register(Block)
    def _eval_block(self, node: Block) -> Any:
        return self.execute(node)

    @evaluate.register(Call)
    def _eval_call(self, node: Call) -> Any:
        callee = self.evaluate(node.callee)
        if not callable(callee):
            raise handler.error("Call to non-function {}".format(callee))
        if len(node.args) != callee.arity:
            raise handler.error("Wrong number of arguments")
        args = [self.evaluate(arg) for arg in node.args]
        try:
            return callee(self, *args)
        except SubmitError as e:
            return e.res

    @evaluate.register(Exam)
    def _eval_exam(self, node: Exam) -> Any:
        cond = self.evaluate(node.cond)
        if cond:
            if isinstance(node.pass_stmt, Block):
                with self.scope():
                    return self.execute(node.pass_stmt)
            else:
                return self.execute(node.pass_stmt)
        elif node.fail_stmt:
            if isinstance(node.fail_stmt, Block):
                with self.scope():
                    return self.execute(node.fail_stmt)
            else:
                return self.execute(node.fail_stmt)
        else:
            return None

    @evaluate.register(ExprStmt)
    def _eval_expr_stmt(self, node: ExprStmt) -> Any:
        return self.evaluate(node.expr)

    @evaluate.register(Submit)
    def _eval_submit(self, node: Submit) -> NoReturn:
        raise SubmitError(self.evaluate(node.expr))

    @evaluate.register(Work)
    def _eval_work(self, node: Work) -> Any:
        work = CHWork(None, node)
        work.closure = Env(self.env, {node.identifier: work})
        self.env = self.env.assign(node.identifier, work)
        return work

    @evaluate.register(Redo)
    def _eval_redo(self, node: Redo) -> Any:
        result = []
        with self.scope():
            for i in self.evaluate(node.interval):
                self.env = Env(self.env).assign(node.identifier, i)
                result.append(self.execute(node.body))
        return result

    @evaluate.register(Interval)
    def _eval_interval(self, node: Interval) -> Any:
        start = self.evaluate(node.start)
        end = self.evaluate(node.end)
        if not isinstance(start, CHQuantity) and isinstance(end, CHQuantity):
            raise handler.error(node.dots, "start and end must be CHQuantity")
        tmp = start + end
        unit = tmp.unit
        formula = tmp.formula
        return (
            CHQuantity(formula, Decimal(i), unit)
            for i in range(int(start.magnitude), int(end.magnitude))
        )

    @evaluate.register(Conversion)
    def _eval_conversion(self, node: Conversion) -> Any:
        context = {}
        for rxn in node.reaction:
            balanced = rxn.balanced
            if self.env.lookup("show_balanced_equation"):
                print(balanced)
            context.update(balanced.context)
        unit = node.unit
        if isinstance(unit, Formula):
            unit = FormulaUnit([Formula(unit.terms)])
        return self.evaluate(node.value).to(unit, context)

    @evaluate.register(Assign)
    def _eval_assign(self, node: Assign) -> Any:
        val = self.evaluate(node.val)
        self.env = self.env.assign(node.name, val)
        return val

    @evaluate.register(Variable)
    def _eval_variable(self, node: Variable) -> Any:
        try:
            return self.env.lookup(node.name)
        except CHError as e:
            raise handler.error(e.msg)

    @evaluate.register(Grouping)
    def _eval_grouping(self, node: Grouping) -> Any:
        return self.evaluate(node.expr)

    @evaluate.register(Literal)
    def _eval_literal(self, node: Literal) -> Any:
        # Everything begins here!
        if isinstance(node.value, CHString):
            return node.value.substituted()
        return node.value

    @evaluate.register(Formula)
    def _eval_formula(self, node: Formula) -> Any:
        return node.molecular_mass

    @evaluate.register(Unary)
    def _eval_unary(self, node: Unary) -> Any:
        right = self.evaluate(node.right)
        result = 0
        match node.op:
            case TokenType.ADD:
                result = +right
            case TokenType.SUB:
                result = -right
            case TokenType.INV:
                result = ~right
            case TokenType.NOT:
                result = not right
            case _:
                raise handler.error(node.op, "Invalid unary operator")
        return result

    @evaluate.register(Binary)
    def _eval_binary(self, node: Binary) -> Any:
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        result = 0
        match node.op:
            case TokenType.ADD:
                result = left + right
            case TokenType.SUB:
                result = left - right
            case TokenType.MUL:
                result = left * right
            case TokenType.DIV:
                result = left / right
            case TokenType.MOD:
                result = left % right
            case TokenType.CARET | TokenType.MULMUL:
                result = left**right
            case TokenType.LE:
                result = left <= right
            case TokenType.LT:
                result = left < right
            case TokenType.GE:
                result = left >= right
            case TokenType.GT:
                result = left > right
            case TokenType.EQEQ:
                result = left == right
            case TokenType.NOEQ:
                result = left != right
            case TokenType.AND:
                result = left and right
            case TokenType.OR:
                result = left or right
            case _:
                raise handler.error(node.op, "Unknown operator")
        return result
