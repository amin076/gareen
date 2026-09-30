# Gareen

**Gareen** is an experiment about machine-grown formal mathematics.

Phase 1 deliberately starts tiny. There is no LLM, no agent, no Lean, and no attempt to model modern number theory yet. The goal is to establish one clean boundary:

> The host computer may use its own arithmetic to run Python, but the mathematical world being studied must manipulate its own symbols and rules instead of asking Python to solve the arithmetic for it.

## Phase 1 — symbolic arithmetic core

The object-world contains only:

- `0` — a symbolic zero
- `S(x)` — symbolic successor
- `Add(a, b)` — symbolic addition
- two recursive rewrite rules for addition

The rules are:

```text
Add(a, 0)    -> a
Add(a, S(b)) -> S(Add(a, b))
```

For example, the program represents what humans call two plus three as:

```text
Add(S(S(0)), S(S(S(0))))
```

It then reaches:

```text
S(S(S(S(S(0)))))
```

only by applying the two declared object-world rules. It does **not** evaluate `2 + 3` with Python arithmetic.

## Why this matters

Python still uses CPU arithmetic, Boolean logic, memory addresses, loops, and many other mathematical structures at the **meta-level**. That cannot and need not be removed.

The experiment instead separates:

```text
host / meta-level
    Python, CPU, memory, control flow

object / mathematical level
    Zero, Succ, Add, declared inference/rewrite rules
```

A result counts as derived in Gareen only when its trace is built from the object-world rules.

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python math_world.py
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## What Phase 1 proves — and does not prove

Phase 1 demonstrates that we can build a small symbolic mathematical world whose arithmetic transformations are explicit and auditable.

It does **not** yet:

- discover new theorems
- implement quantified logic or induction
- distinguish interesting from trivial theorems
- use Peano Arithmetic in full
- use Lean or another proof assistant
- use Qwen, LLMs, or multi-agent search

Those belong to later experiments only after this core boundary is trustworthy.
