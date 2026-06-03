# type: ignore
# explicit-test: modes=default,extra; extra=match_guard
value = True  # expect: single_use_var
count: int = 5


# ── default mode: guards checked for implicit booleans ──────────────────────

# -- implicit guard (name) --
match count:
    case _ if count:  # expect: match_guard
        pass
    case _:
        pass

match count:
    case _ if count > 0:  # expect: match_guard@extra
        pass
    case _:
        pass


# -- implicit guard (not + name) --
match count:
    case _ if not count:  # expect: match_guard
        pass
    case _:
        pass

match count:
    case _ if not (count > 0):  # expect: match_guard@extra
        pass
    case _:
        pass


# -- no guard --
match count:
    case _ :
        pass


# -- and --
match count:
    case _ if count and value:  # expect: bool_op, bool_op, match_guard@default, match_guard@default, match_guard@extra
        pass
    case _:
        pass

match count:
    case _ if count > 0 and count < 10:  # expect: match_guard@extra
        pass
    case _:
        pass


# ── --include-extra match_guard: all guards banned ───────────────────────────
# any guard is flagged regardless of explicit vs implicit
# the right pattern is to move the condition into the case body

match count:
    case _ if count > 0:  # expect: match_guard@extra
        pass
    case _:
        pass

match count:
    case _:
        if count > 0:  # clean: logic moved into body
            pass
