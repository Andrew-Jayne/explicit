# type: ignore
# explicit-test: modes=default,extra; extra=lambda
# -- implicit boolean: BoolOp --
checker = lambda first, second: first and second  # expect: lambda, bool_op, bool_op

def checker_explicit(first, second):
    return first and second  # expect: bool_op, bool_op


# -- implicit boolean: UnaryOp(Not) --
negator = lambda value: not value  # expect: lambda

def negator_explicit(value):
    return not value


# -- implicit boolean: ternary with implicit test --
handler = lambda count: 1 if count else 0  # expect: lambda, ternary

def handler_explicit(count):
    if count is not None:
        return 1
    else:
        return 0


# -- clean lambdas: explicit operations --
doubler = lambda num: num * 2  # expect: lambda@extra

upper = lambda text: text.upper()  # expect: lambda@extra

comparator = lambda num: num > 0  # expect: lambda@extra

identity = lambda value: value  # expect: lambda@extra


# -- clean lambdas: method/function calls --
getter = lambda obj: obj.value  # expect: lambda@extra

caller = lambda items: len(items)  # expect: lambda@extra


# ── --include-extra lambda: all lambdas flagged ─────────────────────────────
# with this opt-in, even clean lambdas are flagged

simple_math = lambda num: num + 1  # expect: lambda@extra

simple_call = lambda text: text.upper()  # expect: lambda@extra

def simple_math_explicit(num):
    return num + 1

def simple_call_explicit(text):
    return text.upper()
