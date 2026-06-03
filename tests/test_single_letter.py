# type: ignore
# -- function names --
def f():  # expect: single_letter_var
    pass

def func():
    pass


# -- function parameters --
def func_with_args(x):  # expect: single_letter_var
    pass

def func_with_args(param):
    pass


# -- async function --
async def g():  # expect: single_letter_var
    pass

async def handler():
    pass


# -- class names --
class C:  # expect: single_letter_var
    pass

class Counter:
    pass


# -- variable assignment --
x = 1  # expect: single_letter_var

var = 1


# -- annotated assignment --
y: int = 2  # expect: single_letter_var

count: int = 2


# -- loop variables --
for i in range(10):  # expect: single_letter_var
    pass

for item in range(10):
    pass


# -- tuple unpacking --
a, b = 1, 2  # expect: single_letter_var, single_letter_var

first, second = 1, 2


# -- multiple assignment --
x = y = 0  # expect: single_letter_var, single_letter_var

val = result = 0


# -- exception handler --
try:
    pass
except Exception as e:  # expect: single_letter_var
    pass

try:
    pass
except Exception as err:
    pass


# -- walrus operator --
if (n := 5) > 0:  # expect: single_letter_var
    pass

if (result := 5) > 0:
    pass


# -- underscore excluded (standard for throwaway) --
for _ in range(10):
    pass

_ = "throwaway"
