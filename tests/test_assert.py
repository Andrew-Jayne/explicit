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
assert value  # expect: assert

assert value is True


# -- call --
assert get_value()  # expect: assert

assert get_value() is True


# -- attribute --
assert obj.attr  # expect: assert

assert obj.attr is True


# -- not + name --
assert not value  # expect: assert

assert value is False


# -- not + compare --
assert not (count > 0)


# -- bool constants --
assert True

assert False


# -- comparisons --
assert count > 0

assert count != 0


# -- and --
assert value and other  # expect: assert, assert, bool_op, bool_op

assert count > 0 and count < 10


# -- or --
assert value or other  # expect: assert, assert, bool_op, bool_op

assert value is True or other is True
