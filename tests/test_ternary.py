# type: ignore
value = True
other = False
count: int = 5


class _Obj:
    attr: bool = True


obj = _Obj()


def get_value() -> bool:
    return False


# -- basic --
result = 1 if value is True else 0  # expect: ternary

result = 1
if value is True:
    result = 1
else:
    result = 0


# -- call --
result = 1 if get_value() is True else 0  # expect: ternary

result = 1
if get_value() is True:
    result = 1
else:
    result = 0


# -- attribute --
result = 1 if obj.attr is True else 0  # expect: ternary

result = 1
if obj.attr is True:
    result = 1
else:
    result = 0


# -- comparison --
result = 1 if count > 0 else 0  # expect: ternary

result = 1
if count > 0:
    result = 1
else:
    result = 0
