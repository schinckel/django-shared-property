from ast import (  # Import,; ImportFrom,; Expr,; alias,
    Add,
    And,
    Assign,
    Attribute,
    BinOp,
    BoolOp,
    Call,
    Compare,
    Constant,
    Eq,
    FunctionDef,
    GeneratorExp,
    Gt,
    GtE,
    If,
    Import,
    Is,
    IsNot,
    Lambda,
    List,
    Load,
    Lt,
    LtE,
    Module,
    Name,
    Not,
    NotEq,
    Num,
    Return,
    Store,
    Str,
    Tuple,
    UnaryOp,
    While,
    alias,
    arg,
    arguments,
    comprehension,
    fix_missing_locations,
    stmt,
)
from enum import Enum

OPERATORS = {
    "<": Lt,
    "<=": LtE,
    "=": Eq,
    "!=": NotEq,
    ">": Gt,
    ">=": GtE,
}

_extensions = {}


class Parser(object):
    def __init__(self, function):
        expression = function(None)
        if getattr(expression, "copy", None):
            expression = expression.copy()
        func_code = getattr(function, "__code__", None) or function.func_code
        self.file = {
            "lineno": func_code.co_firstlineno,
            "filename": func_code.co_filename,
            "col_offset": 0,
            "ctx": Load(),
        }
        self.file_store = dict(self.file, ctx=Store())
        self.expression = expression
        self.imports = set()
        body = self.build_expression(expression)
        if isinstance(body, list):
            pass
        elif not isinstance(body, stmt):
            body = [Return(value=body, **self.file)]
        else:
            body = [body]

        self.ast = Module(
            # body=self.imports + [
            body=[
                FunctionDef(
                    name=func_code.co_name,
                    args=arguments(
                        args=[arg(arg="self", annotation=None)],  # function.func_code.co_varnames
                        defaults=[],
                        vararg=None,
                        kwarg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        posonlyargs=[],
                    ),
                    kwarg=[],
                    kw_defaults=[],
                    vararg=[],
                    kwonlyargs=[],
                    body=[
                        Import(names=[alias(name=imp, **self.file)], **self.file)
                        for imp in self.imports
                    ] + body,
                    decorator_list=[],
                ),
            ],
            type_ignores=[],
            **self.file,
        )
        # import pdb; pdb.set_trace()
        fix_missing_locations(self.ast)
        self.code = compile(self.ast, mode="exec", filename=self.file["filename"])

    def build_expression(self, expression):
        if expression is None:
            return Constant(value=None, **self.file)
        handler_name = "handle_{}".format(expression.__class__.__name__.lower())

        if handler_name in _extensions:
            return _extensions[handler_name](self, expression)

        return getattr(self, handler_name)(expression)

    def handle_case(self, case):
        # We can have N When expressions, and then (optionally) one that is the default.
        return self.handle_when(*case.get_source_expressions())

    def handle_when(self, when, *others):
        test, body = when.get_source_expressions()
        if others:
            if others[0].__class__.__name__ == "When":
                orelse = [self.handle_when(*others)]
            else:
                # Can we ever have other expressions after the default?
                orelse = [Return(value=self.build_expression(others[0]), **self.file)]
        else:
            orelse = []

        return If(
            test=self.build_expression(test),
            body=[Return(value=self.build_expression(body), **self.file)],
            orelse=orelse,
            **self.file,
        )

    def handle_bool(self, boolean):
        return Constant(value=boolean, **self.file)

    def handle_q(self, q):
        if not q.children:
            expr = Name(id="True", **self.file)
        elif len(q.children) == 1:
            expr = self._attr_lookup(*q.children[0])
        elif q.connector == "AND":
            expr = Call(
                func=Name(id="all", **self.file),
                args=[List(elts=[self._attr_lookup(k, v) for k, v in q.children], **self.file)],
                keywords=[],
                kwonlyargs=[],
                **self.file,
            )
        else:  # q.connector == 'OR'
            expr = Call(
                func=Name(id="any", **self.file),
                args=[List(elts=[self._attr_lookup(k, v) for k, v in q.children], **self.file)],
                keywords=[],
                kwonlyargs=[],
                **self.file,
            )

        if q.negated:
            return UnaryOp(op=Not(), operand=expr, **self.file)

        return expr

    def handle_concat(self, concat):
        return self.build_expression(*concat.get_source_expressions())

    def handle_concatpair(self, pair):
        a, b = pair.get_source_expressions()
        return BinOp(left=self.build_expression(a), op=Add(), right=self.build_expression(b), **self.file)

    def handle_f(self, f):
        # Do we need to use .attname here?
        # What about transforms/lookups?
        f.contains_aggregate = False
        if "__" in f.name:
            self.imports.add('functools')

            return Call(
                func=Attribute(value=Name(id='functools', **self.file), attr='reduce', **self.file),
                args=[
                    Lambda(
                        args=arguments(
                            posonlyargs=[],
                            args=[arg(arg='x', **self.file), arg(arg='y', **self.file)],
                            kwonlyargs=[],
                            kw_defaults=[],
                            defaults=[]
                        ),
                        body=Call(
                            func=Name(id='getattr', **self.file),
                            args=[
                                Name(id='x', **self.file),
                                Name(id='y', **self.file),
                                Constant(value=None, **self.file),
                            ],
                            keywords=[],
                            **self.file
                        ),
                        **self.file
                    ),
                    List(
                        elts=[
                            Constant(value=x, **self.file)
                            for x in f.name.split('__')
                        ],
                        **self.file
                    ),
                    Name(id='self', **self.file),
                ],
                keywords=[],
                **self.file,
            )

            left, *parts = f.name.split('__')
            expression = Attribute(value=Name(id='self', **self.file), attr=left, **self.file)
            while parts:
                left, *parts = parts
                expression = Attribute(value=expression, attr=left, **self.file)
            return expression

            # We need to chain a bunch of attr lookups, returning None
            # if any of them give us a None, we should be returning a None.
            #

            # .  while x is not None and parts:
            # .      x = getattr(x, parts.pop(0), None)
            #   return x
            return [
                Assign(
                    targets=[Name(id="source", **self.file_store)], value=Name(id="self", **self.file), **self.file
                ),
                Assign(
                    targets=[Name(id="parts", **self.file_store)],
                    value=Call(
                        func=Attribute(value=Constant(value=f.name, **self.file), attr="split", **self.file),
                        args=[Constant(value="__", **self.file)],
                        keywords=[],
                        kwonlyargs=[],
                        **self.file,
                    ),
                    **self.file,
                ),
                While(
                    test=BoolOp(
                        op=And(),
                        values=[
                            Compare(
                                left=Name(id="source", **self.file),
                                ops=[IsNot()],
                                comparators=[Constant(value=None, **self.file)],
                                **self.file,
                            ),
                            Name(id="parts", **self.file),
                        ],
                        **self.file,
                    ),
                    body=[
                        Assign(
                            targets=[Name(id="source", **self.file_store)],
                            value=Call(
                                func=Name(id="getattr", **self.file),
                                args=[
                                    Name(id="source", **self.file),
                                    Call(
                                        func=Attribute(value=Name(id="parts", **self.file), attr="pop", **self.file),
                                        args=[Constant(value=0, **self.file)],
                                        keywords=[],
                                        kwonlyargs=[],
                                        **self.file,
                                    ),
                                    Constant(value=None, **self.file),
                                ],
                                keywords=[],
                                kwonlyargs=[],
                                **self.file,
                            ),
                            **self.file,
                        ),
                    ],
                    orelse=[],
                    **self.file,
                ),
                Return(value=Name(id="source", **self.file), **self.file),
            ]
        return Attribute(value=Name(id="self", **self.file), attr=f.name, **self.file)

    def handle_value(self, value):
        if isinstance(value.value, Enum):
            return Attribute(
                value=Name(id=value.value.__class__.__name__, **self.file),
                attr=value.value.name,
                **self.file,
            )

        if isinstance(value.value, str):
            return Str(s=value.value, **self.file)

        if value.value is None:
            return Constant(value=None, **self.file)

        if isinstance(value.value, int):
            return Num(n=value.value, **self.file)

        if isinstance(value.value, bool):
            return Constant(value=value.value, **self.file)

        raise ValueError("Unhandled Value")

    def _handle_call_factory(func):
        def handle_call(self, expression):
            return Call(
                func=Attribute(
                    value=self.build_expression(*expression.get_source_expressions()), attr=func, **self.file
                ),
                args=[],
                keywords=[],
                kwonlyargs=[],
                **self.file,
            )

        return handle_call

    handle_upper = _handle_call_factory("upper")
    handle_lower = _handle_call_factory("lower")

    def handle_expressionwrapper(self, expression):
        return self.build_expression(*expression.get_source_expressions())

    def handle_combinedexpression(self, expression):
        return Compare(
            left=self.build_expression(expression.lhs),
            ops=[OPERATORS[expression.connector](**self.file)],
            comparators=[self.build_expression(expression.rhs)],
            **self.file,
        )

    # This is commented out because it only supports one function.
    # def handle_func(self, expression):
    #     func = expression.extra.get('function') or expression.function
    #     if func in {'current_timestamp', 'now'}:
    #         self.imports.append(Import(names=[alias(name='django.utils')]))
    #         return Call(
    #             func=Attribute(
    #                 value=Attribute(
    #                     value=Attribute(
    #                         value=Name('django', **self.file),
    #                         attr='utils',
    #                         **self.file
    #                     ),
    #                     attr='timezone',
    #                     **self.file
    #                 ),
    #                 attr='now',
    #                 **self.file
    #             ),
    #             args=[],
    #             keywords=[],
    #             **self.file,
    #         )
    #         return Call(func=Name(id='utcnow', **self.file), args=[], keywords=[], **self.file)

    def handle_coalesce(self, expression):
        """
        next(
            itertools.chain(
                (x for x in expression.get_source_expressions() where x is not None),
                (None,)
            )
        )
        """
        expressions = List(
            elts=[self.build_expression(exp) for exp in expression.get_source_expressions()],
            **self.file,
        )

        return Call(
            func=Name(id="next", **self.file),
            args=[
                GeneratorExp(
                    elt=Name(id="x", **self.file),
                    generators=[
                        comprehension(
                            target=Name(id="x", **(dict(self.file, ctx=Store()))),
                            iter=expressions,
                            ifs=[
                                Compare(
                                    left=Name(id="x", **self.file),
                                    ops=[IsNot()],
                                    comparators=[Constant(value=None, **self.file)],
                                ),
                            ],
                            is_async=False,
                            **self.file,
                        )
                    ],
                    **self.file,
                ),
                Tuple(elts=[Constant(value=None, **self.file)], **self.file),
            ],
            keywords=[],
            **self.file,
        )

    def handle_exact(self, exact):
        left, right = exact.get_source_expressions()
        return Compare(
            left=self.build_expression(left),
            ops=[Eq(**self.file)],
            comparators=[self.build_expression(right)],
            **self.file
        )

    def _attr_lookup(self, attr, value):
        if "__" not in attr:
            return Compare(
                left=Attribute(value=Name(id="self", **self.file), attr=attr, **self.file),
                ops=[Eq()],
                comparators=[self.build_expression(value)],
                **self.file,
            )

        attr, lookup = attr.split("__", 1)

        if lookup == "isnull":
            return Compare(
                left=Attribute(value=Name(id="self", **self.file), attr=attr, **self.file),
                ops=[Is() if value else IsNot()],
                comparators=[Constant(value=None, **self.file)],
                **self.file,
            )

        if lookup == "exact":
            return self._attr_lookup(attr, value)

        raise ValueError("Unhandled attr lookup")


class register:
    def __init__(self, func):
        if isinstance(func, str):
            self.name = f'handle_{func}'
        else:
            name = func.__code__.co_name
            if not name.startswith('handle_'):
                name = f'handle_{name}'
            _extensions[name] = func

    def __call__(self, func):
        _extensions[self.name] = func
