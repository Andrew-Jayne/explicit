# type: ignore

# -- should flag: defined once, called once --
def helper():
    return 42

result = helper()


# -- should flag: nested single-use helper --
def outer():
    def inner_helper():
        return 99

    return inner_helper()


# -- should NOT flag: called more than once --
def utility():
    return 42

a = utility()
b = utility()


# -- should NOT flag: never called (0 references, not 1) --
def unused_func():
    pass


# -- should flag: my_decorator itself is only referenced once (as a decorator) --
# -- should NOT flag: decorated has a decorator --
def my_decorator(fn):
    return fn

@my_decorator
def decorated():
    return 1

decorated()


# -- should NOT flag: class method --
class MyClass:
    def method(self):
        return 42

    def other(self):
        return self.method()


# -- should NOT flag: dunder function --
def __special__():
    return "special"

__special__()


# -- should flag: async function defined once, used once --
async def async_helper():
    return 1

await async_helper()


# -- should NOT flag: multiple definitions (conditional) --
if True:
    def conditional():
        return 1
else:
    def conditional():
        return 2

conditional()


# -- should flag: passed as callback (still single reference) --
def handler():
    print("handling")

register(handler)
