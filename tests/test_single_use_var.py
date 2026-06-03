# type: ignore

# -- should flag: assigned once, used once --
result = int("42")  # expect: single_use_var
print(result)

temp = [1, 2, 3]  # expect: single_use_var
len(temp)


# -- should flag: inside a function scope --
def process():
    data = fetch_data()  # expect: single_use_var
    return data


def transform():
    value: int = compute()  # expect: single_use_var
    return value


# -- should NOT flag: used more than once --
items = get_items()
process_items(items)
save_items(items)


# -- should NOT flag: assigned more than once --
x = 1  # expect: single_letter_var
x = 2  # expect: single_letter_var
print(x)


# -- should NOT flag: unused (0 references, not 1) --
unused = something()


# -- should NOT flag: tuple unpacking --
first, second = get_pair()
print(first)


# -- should NOT flag: loop variable --
for item in range(10):
    print(item)


# -- should NOT flag: function parameter --
def func(param):
    return param


# -- should NOT flag: dunder name --
__version__ = "1.0"


# -- should NOT flag: constant (ALL_CAPS) used once --
MAX_RETRIES = 3
print(MAX_RETRIES)

DEFAULT_TIMEOUT: float = 1.5
connect(DEFAULT_TIMEOUT)


# -- should NOT flag: underscore --
_ = throwaway()


# -- should NOT flag: augmented assignment --
counter = 0
counter += 1


# -- should NOT flag: global declaration --
def uses_global():
    global shared
    shared = 42


# -- should NOT flag: nonlocal declaration --
def uses_nonlocal():
    captured = 0
    def modifier():  # expect: single_use_func
        nonlocal captured
        captured = 1
    modifier()  # (modifier itself flagged below as single-use func)


# -- should NOT flag: nonlocal modified then returned --
def nonlocal_then_use():
    value = 0
    def bump():  # expect: single_use_func
        nonlocal value
        value = 99
    bump()
    return value


# -- should NOT flag: conditional definition (multiple defs) --
def branching(flag):
    if flag:  # expect: if
        val = 1
    else:
        val = 2
    return val


# -- should NOT flag: annotated assignment without value --
declared: int


# -- should flag: scoped independently (same name in different functions) --
def scope_a():
    throwaway = calculate()  # expect: single_use_var
    return throwaway


def scope_b():
    throwaway = other_calc()  # expect: single_use_var
    return throwaway
