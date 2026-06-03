# type: ignore
value = True
other = False
count: int = 5


class _Obj:
    attr: bool = True


obj = _Obj()


def get_value() -> bool:
    return False


# -- name --
while value:  # expect: while
    break
while value is True:
    break


# -- call --
while get_value():  # expect: while
    break
while get_value() is True:
    break


# -- attribute --
while obj.attr:  # expect: while
    break
while obj.attr is True:
    break


# -- not + name --
while not value:  # expect: while
    break
while value is False:  # pyright: ignore[reportUnnecessaryComparison]
    break


# -- not + compare --
while not (count > 0):
    break


# -- bool constants --
while True:
    break
while False:
    break


# -- comparisons --
while count > 0:
    break
while count != 0:  # pyright: ignore[reportUnnecessaryComparison]
    break


# -- and --
while value and other:  # expect: while, while, bool_op, bool_op
    break
while count > 0 and count < 10:
    break


# -- or --
while value or other:  # expect: while, while, bool_op, bool_op
    break
while value is True or other is True:  # pyright: ignore[reportUnnecessaryComparison]
    break
