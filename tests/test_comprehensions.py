# type: ignore
items = [1, 2, 3, 4, 5]
pairs = [("a", 1), ("b", 2)]
mixed: list[int | None] = [1, None, 2, None, 3]


# -- list comp --
result = [item for item in items]  # expect: list_comp

result: list[int] = []
for item in items:
    result.append(item)


# -- set comp --
unique = {item for item in items}  # expect: set_comp

unique: set[int] = set()
for item in items:
    unique.add(item)


# -- dict comp --
lookup = {key: val for key, val in pairs}  # expect: dict_comp

lookup = {}
for key, val in pairs:
    lookup[key] = val


# -- generator --
total = sum(item * 2 for item in items)  # expect: generator

total = 0
for item in items:
    total += item * 2


# -- explicit if filter --
filtered = [item for item in items if item > 0]  # expect: list_comp

filtered: list[int] = []
for item in items:
    if item > 0:
        filtered.append(item)


# -- implicit if filter --
filtered = [item for item in mixed if item]  # expect: list_comp, comprehension

filtered = []
for item in mixed:
    if item is not None:
        filtered.append(item)


# -- filter(None) --
cleaned = list(filter(None, mixed))  # expect: filter

cleaned: list[int | None] = []
for item in mixed:
    if item is not None:
        cleaned.append(item)


# -- nested generators --
nested = [item for item in items for other in items]  # expect: list_comp

nested: list[int] = []
for item in items:
    for other in items:
        nested.append(item)
