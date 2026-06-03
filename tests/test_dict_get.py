# type: ignore
# explicit-test: modes=default,extra; extra=dict_get
config = {"host": "localhost", "port": 8080}


# ── default mode: dict_get never fires (no default variant) ──────────────────
# every .get() below is flagged only when --include-extra dict_get is on


# -- single arg --
config.get("host")  # expect: dict_get@extra

# -- key + positional default --
config.get("host", "localhost")  # expect: dict_get@extra

# -- chained .get() flags each call --
config.get("a").get("b")  # expect: dict_get@extra, dict_get@extra


# ── should NOT flag (in any mode) ────────────────────────────────────────────

# -- explicit keyed access --
config["host"]

# -- zero args --
config.get()

# -- more than two positional args --
config.get("a", "b", "c")

# -- keyword argument present (e.g. requests-style .get(url, timeout=...)) --
config.get("host", default="localhost")

# -- different attribute name --
config.keys()

# -- starred args --
config.get(*["host"])


# -- get() as a bare function, not a method, is never a dict_get --
def get(name):  # expect: single_use_func
    return name


get("host")
