# type: ignore
value = True
other = False
count: int = 5


# -- and with implicit operands --
result = value and other  # expect: bool_op, bool_op

result = value is True and other is False


# -- or with implicit operands --
result = value or other  # expect: bool_op, bool_op

result = value is True or other is True


# -- mixed: some implicit, some explicit --
result = value and count > 0  # expect: bool_op

result = value is True and count > 0


# -- and with explicit comparisons --
result = count > 0 and count < 10

result = value is True and value is False


# -- or with explicit comparisons --
result = count > 0 or count < 10

result = value is True or value is False


# -- chained --
result = value and other and value  # expect: bool_op, bool_op, bool_op

result = count > 0 and count < 10 and count != 5
