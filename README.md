# explicit

A semantic clarity enforcer for production Python. 

`explicit` flags code where the author's intent is ambiguous — patterns that force the next reader (or LLM) to guess what was meant instead of knowing.


## What it catches

| Check | What's ambiguous | What to write instead |
|---|---|---|
| **Implicit booleans** in `if`/`while`/`assert` | `if items:` — checking length? nullness? | `if len(items) > 0:` or `if items is not None:` |
| **Ternary expressions** | `x if condition else y` — buries control flow | Explicit `if`/`else` block |
| **Boolean operators** | `a and b` with non-boolean operands | Explicit comparisons for each operand |
| **List/set/dict comprehensions** | Dense, nested logic in a single expression | Explicit `for` loop |
| **Generator expressions** | Same problem, lazily evaluated | Explicit generator function or loop |
| **Lambda expressions** | Anonymous logic with no name to describe intent | Named function |
| **`filter(None, ...)`** | Implicit truthiness as a filter predicate | Explicit filter function |
| **Match/case guards** | Logic hidden in pattern matching syntax | Move logic to case body |
| **Single-letter variables** | `x`, `d`, `n` — no semantic meaning | Descriptive names |
| **Single-use variables** | `result = compute(); return result` — pointless indirection | Inline the expression |
| **Single-use functions** | Helper called exactly once | Inline at the call site |

## Install

No install required. Run directly from GitHub using [uv](https://docs.astral.sh/uv/):

```bash
uvx --from "git+https://github.com/Andrew-Jayne/explicit" explicit <path>
```

Or if you have the repo cloned:

```bash
uv run explicit <path>
```

## Usage

```bash
# Analyze a file
explicit myfile.py

# Analyze a directory
explicit src/

# JSON output (for CI/tooling)
explicit . --format json

# Skip specific checks
explicit . --exclude-type ternary --exclude-type single_use_var

# Statistics only
explicit . --stats-only

# Strict mode: ban all lambdas and match guards
explicit . --disallow-lambda --disallow-logic-in-match
```

## Output formats

**Text**: grouped by file, color-coded by check type, with inline context.

**JSON**" one object per check. Suitable for CI integration, editor plugins, or piping into other tools.

**CSV**: Headers: `File, Line, Column, Type, Code, Context`.

## Philosophy

The Zen of Python says "explicit is better than implicit." This tool enforces that line.

Most of the patterns that this tool flags exist for one reason: saving keystrokes.That trade made more sense when you were typing every character yourself. It makes no sense now. Your editor has autocomplete. Your AI agent will write the verbose version just as fast as the clever one. The keystrokes are free. The ambiguity is not.

The goal is not style, it's semantic precision. Code should say what it means so that the next person (or LLM) reading it can understand the intent without guessing.

## Requirements

Python >= 3.14
