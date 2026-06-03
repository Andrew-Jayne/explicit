# type: ignore
value = True
other = False
count: int = 5
items = [1, 2, 3]


class _Obj:
    attr: bool = True


obj = _Obj()


def get_value() -> bool:
    return False


# -- name --
if not value:  # expect: if
    pass
if value:  # expect: if
    pass

# -- call --
if get_value():  # expect: if
    pass
if get_value() is True:
    pass
if not get_value():  # expect: if
    pass
if get_value() is False:
    pass

# -- attribute --
if obj.attr:  # expect: if
    pass
if obj.attr is True:
    pass

# -- subscript --
if items[0]:  # expect: if
    pass
if items[0] > 0:
    pass

# -- not + compare --
if not count:  # expect: if
    pass
if not (count > 0):
    pass

# -- bool constants --
if True:
    pass
if False:
    pass  # pyright: ignore[reportUnreachable]

# -- comparisons --
if value is True:
    pass
if value is False:  # pyright: ignore[reportUnnecessaryComparison]
    pass
if count > 0:
    pass
if count == 5:
    pass
if count != 0:  # pyright: ignore[reportUnnecessaryComparison]
    pass
if count in items:
    pass

# -- and --
if value and other:  # expect: if, if, bool_op, bool_op
    pass
if count > 0 and count < 10:
    pass
if not value and not other:  # expect: if, if, bool_op, bool_op
    pass
if value is True and other is False:
    pass

# -- or --
if value or other:  # expect: if, if, bool_op, bool_op
    pass
if value is True or other is True:  # pyright: ignore[reportUnnecessaryComparison]
    pass

# -- mixed BoolOp --
if value and count > 0:  # expect: if, bool_op
    pass
if value is True and count > 0:
    pass

# -- walrus --
if (result := get_value()):  # expect: if
    pass
if (result := get_value()) is True:
    pass

# -- elif --
if count > 0:
    pass
elif get_value():  # expect: if
    pass

if count > 0:
    pass
elif get_value() is True:
    pass
