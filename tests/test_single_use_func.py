# type: ignore

# -- should flag: defined once, called once --
def helper():  # expect: single_use_func
    return 42

result = helper()


# -- should flag: nested single-use helper --
def outer():
    def inner_helper():  # expect: single_use_func
        return 99

    return inner_helper()


# -- should NOT flag: called more than once --
def utility():
    return 42

a = utility()  # expect: single_letter_var
b = utility()  # expect: single_letter_var


# -- should NOT flag: never called (0 references, not 1) --
def unused_func():
    pass


# -- should flag: my_decorator itself is only referenced once (as a decorator) --
# -- should NOT flag: decorated has a decorator --
def my_decorator(fn):  # expect: single_use_func
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


# -- should NOT flag: async functions are excluded --
async def async_helper():
    return 1

await async_helper()


# -- should NOT flag: function named 'main' is excluded --
def main():
    pass

main()


# -- should NOT flag: entry point called only from __name__ guard --
def cli():
    pass


if __name__ == "__main__":
    cli()


# -- should NOT flag: multiple definitions (conditional) --
if True:
    def conditional():
        return 1
else:
    def conditional():
        return 2

conditional()


# -- should flag: passed as callback (still single reference) --
def handler():  # expect: single_use_func
    print("handling")

register(handler)
