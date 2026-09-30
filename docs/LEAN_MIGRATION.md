# Lean Migration Roadmap

## Status

Phases 1–11 created a complete small formal world in Python. That work is kept,
but no longer expanded as a competing proof-assistant kernel.

## Migration rule

When a new mathematical feature is needed, first ask:

> Does Lean/Mathlib already formalize this?

If yes, Gareen should import and use it rather than reimplement it.

Examples that should now come from Mathlib include:

- order relations;
- divisibility;
- primes;
- gcd/lcm;
- modular arithmetic;
- finite sets;
- algebraic structures;
- elementary and advanced number theory.

## Local setup

Lean's official installer uses `elan`. This repository pins its toolchain in
`lean-toolchain`, so once `elan` is installed:

```text
lake update
lake exe cache get
lake build
```

The Mathlib cache avoids rebuilding Mathlib locally.

## Python bridge

With Lean available:

```text
python lean_bridge.py --ci-demo
python lean_research.py --limit 3
```

The first command checks representative Gareen propositions directly in Lean.
The second runs Gareen's conjecture generator and sends candidates to Lean.

## Compatibility policy

- Existing Python tests must continue to pass.
- New research claims should receive Lean verification.
- Python and Lean representations may coexist during migration.
- We will migrate the *trust boundary* first, then gradually migrate the
  mathematical knowledge representation.
- No effort should be spent recreating mature Mathlib domains unless the goal
  is explicitly educational or experimental.
