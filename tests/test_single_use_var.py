# type: ignore

# -- should flag: assigned once, used once --
result = int("42")
print(result)

temp = [1, 2, 3]
len(temp)


# -- should flag: inside a function scope --
def process():
    data = fetch_data()
    return data


def transform():
    value: int = compute()
    return value


# -- should NOT flag: used more than once --
items = get_items()
process_items(items)
save_items(items)


# -- should NOT flag: assigned more than once --
x = 1
x = 2
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
    def modifier():
        nonlocal captured
        captured = 1
    modifier()


# -- should NOT flag: nonlocal modified then returned --
def nonlocal_then_use():
    value = 0
    def bump():
        nonlocal value
        value = 99
    bump()
    return value


# -- should NOT flag: conditional definition (multiple defs) --
def branching(flag):
    if flag:
        val = 1
    else:
        val = 2
    return val


# -- should NOT flag: annotated assignment without value --
declared: int


# -- should flag: scoped independently (same name in different functions) --
def scope_a():
    throwaway = calculate()
    return throwaway


def scope_b():
    throwaway = other_calc()
    return throwaway
