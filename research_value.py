"""Research-value scoring for Gareen.

Formal truth is necessary but not sufficient for a useful mathematical
research result.  This module separates *verification* from *interestingness*.

The main design rules are:

1. Ground numerical examples are evidence for conjecture formation, not
   research discoveries.
2. Statements explained entirely by Gareen's primitive arithmetic rewrites
   are routine, even if they contain variables.
3. A candidate that is reachable from existing verified knowledge in at most
   two local theorem-rewrite steps is too close to known knowledge to consume
   scarce research budget.
4. Among the remaining candidates, prefer generality, compression of prior
   facts, structural reuse across the current frontier, and mathematical
   novelty.

The local derivation-distance check is deliberately conservative.  It is a
small rewrite search over already verified equations; it is NOT a claim about
minimal proof length in Lean or in mathematics.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Iterable, Optional, Sequence

from artificial_mathematician import ResearchConjecture
from math_world import (
    Add,
    Eq,
    Expr,
    ForAll,
    Formula,
    KnowledgeState,
    Mul,
    Succ,
    Var,
    Zero,
    free_vars_expr,
    normalize,
)


@dataclass(frozen=True)
class ResearchValueAssessment:
    score: int
    accepted: bool
    reason: str
    variable_count: int
    primitive_rewrite_equivalent: bool
    primitive_rewrite_steps: Optional[int]
    known_derivation_distance: Optional[int]
    subsumed_known_results: int
    reuse_potential: int
    structural_richness: int


@dataclass(frozen=True)
class RankedConjecture:
    conjecture: ResearchConjecture
    assessment: ResearchValueAssessment


def _expr_size(expr: Expr) -> int:
    if isinstance(expr, (Zero, Var)):
        return 1
    if isinstance(expr, Succ):
        return 1 + _expr_size(expr.value)
    if isinstance(expr, (Add, Mul)):
        return 1 + _expr_size(expr.left) + _expr_size(expr.right)
    return 1


def _node_kinds(expr: Expr) -> frozenset[str]:
    if isinstance(expr, Zero):
        return frozenset({"zero"})
    if isinstance(expr, Var):
        return frozenset({"var"})
    if isinstance(expr, Succ):
        return frozenset({"succ"}) | _node_kinds(expr.value)
    if isinstance(expr, Add):
        return (
            frozenset({"add"})
            | _node_kinds(expr.left)
            | _node_kinds(expr.right)
        )
    if isinstance(expr, Mul):
        return (
            frozenset({"mul"})
            | _node_kinds(expr.left)
            | _node_kinds(expr.right)
        )
    return frozenset({type(expr).__name__})


def _children(expr: Expr) -> tuple[Expr, ...]:
    if isinstance(expr, Succ):
        return (expr.value,)
    if isinstance(expr, (Add, Mul)):
        return (expr.left, expr.right)
    return ()


def _rebuild(expr: Expr, children: Sequence[Expr]) -> Expr:
    if isinstance(expr, Succ):
        return Succ(children[0])
    if isinstance(expr, Add):
        return Add(children[0], children[1])
    if isinstance(expr, Mul):
        return Mul(children[0], children[1])
    return expr


def _contains_subexpr(container: Expr, needle: Expr) -> bool:
    if container == needle:
        return True
    return any(_contains_subexpr(child, needle) for child in _children(container))


def _split_universal(formula: Formula) -> tuple[tuple[Var, ...], Formula]:
    variables: list[Var] = []
    current = formula
    while isinstance(current, ForAll):
        variables.append(current.variable)
        current = current.body
    return tuple(variables), current


@dataclass(frozen=True)
class _RewriteRule:
    left: Expr
    right: Expr
    variables: frozenset[Var]


def _rules_from_state(state: KnowledgeState) -> tuple[_RewriteRule, ...]:
    rules: list[_RewriteRule] = []
    formulas = [theorem.statement for theorem in state.theorems.values()]

    for formula in formulas:
        variables, body = _split_universal(formula)
        if not isinstance(body, Eq):
            continue
        rules.append(
            _RewriteRule(
                left=body.left,
                right=body.right,
                variables=frozenset(variables),
            )
        )
    return tuple(rules)


def _match(
    pattern: Expr,
    target: Expr,
    variables: frozenset[Var],
    env: dict[Var, Expr],
) -> bool:
    if isinstance(pattern, Var) and pattern in variables:
        existing = env.get(pattern)
        if existing is None:
            env[pattern] = target
            return True
        return existing == target

    if type(pattern) is not type(target):
        return False

    if isinstance(pattern, Var):
        return pattern == target
    if isinstance(pattern, Zero):
        return True
    if isinstance(pattern, Succ):
        return _match(pattern.value, target.value, variables, env)
    if isinstance(pattern, (Add, Mul)):
        return (
            _match(pattern.left, target.left, variables, env)
            and _match(pattern.right, target.right, variables, env)
        )
    return pattern == target


def _instantiate(expr: Expr, env: dict[Var, Expr]) -> Expr:
    if isinstance(expr, Var):
        return env.get(expr, expr)
    if isinstance(expr, Zero):
        return expr
    if isinstance(expr, Succ):
        return Succ(_instantiate(expr.value, env))
    if isinstance(expr, Add):
        return Add(_instantiate(expr.left, env), _instantiate(expr.right, env))
    if isinstance(expr, Mul):
        return Mul(_instantiate(expr.left, env), _instantiate(expr.right, env))
    return expr


def _root_rewrites(expr: Expr, rule: _RewriteRule) -> tuple[Expr, ...]:
    results: list[Expr] = []
    for source, target in (
        (rule.left, rule.right),
        (rule.right, rule.left),
    ):
        env: dict[Var, Expr] = {}
        if _match(source, expr, rule.variables, env):
            results.append(_instantiate(target, env))
    return tuple(results)


def _rewrite_anywhere(expr: Expr, rule: _RewriteRule) -> tuple[Expr, ...]:
    results: set[Expr] = set(_root_rewrites(expr, rule))
    children = _children(expr)

    for index, child in enumerate(children):
        for rewritten_child in _rewrite_anywhere(child, rule):
            updated = list(children)
            updated[index] = rewritten_child
            results.add(_rebuild(expr, updated))

    return tuple(results)


def _primitive_normal_form(expr: Expr) -> tuple[Expr, int]:
    normal, trace = normalize(expr, max_steps=2000)
    return normal, len(trace)


def primitive_rewrite_distance(left: Expr, right: Expr) -> Optional[int]:
    """Return primitive rewrite distance when both sides normalize identically."""

    try:
        left_normal, left_steps = _primitive_normal_form(left)
        right_normal, right_steps = _primitive_normal_form(right)
    except RuntimeError:
        return None

    if left_normal != right_normal:
        return None
    return left_steps + right_steps


def known_derivation_distance(
    conjecture: ResearchConjecture,
    state: KnowledgeState,
    *,
    max_steps: int = 2,
    max_states: int = 2048,
) -> Optional[int]:
    """Search for a short consequence of already verified Gareen theorems.

    Both raw and primitive-normalized expression shapes are retained. This is
    important for detecting short chains such as x = x * 1 = 1 * x, where
    aggressively normalizing the middle expression would erase the shape
    needed by multiplication commutativity.

    The distance counts uses of already verified theorem equations. Primitive
    normalization is used only as an additional equivalent search state; it
    never replaces the raw state.
    """

    primitive = primitive_rewrite_distance(
        conjecture.body.left,
        conjecture.body.right,
    )
    if primitive is not None:
        return 0

    rules = _rules_from_state(state)
    if not rules or max_steps < 1:
        return None

    try:
        start_normal, _ = _primitive_normal_form(conjecture.body.left)
        target_normal, _ = _primitive_normal_form(conjecture.body.right)
    except RuntimeError:
        start_normal = conjecture.body.left
        target_normal = conjecture.body.right

    targets = {conjecture.body.right, target_normal}
    starts = {conjecture.body.left, start_normal}

    queue = deque((item, 0) for item in starts)
    seen: set[Expr] = set(starts)

    while queue and len(seen) <= max_states:
        current, depth = queue.popleft()
        if current in targets:
            return depth
        if depth >= max_steps:
            continue

        for rule in rules:
            for rewritten in _rewrite_anywhere(current, rule):
                next_states = {rewritten}
                try:
                    normalized, _ = _primitive_normal_form(rewritten)
                    next_states.add(normalized)
                except RuntimeError:
                    pass

                for next_state in next_states:
                    if next_state in targets:
                        return depth + 1
                    if next_state in seen:
                        continue
                    seen.add(next_state)
                    queue.append((next_state, depth + 1))

    return None


def _candidate_matches_formula(
    conjecture: ResearchConjecture,
    formula: Formula,
) -> bool:
    """Whether a conjecture generalizes a known equality instance."""

    _, body = _split_universal(formula)
    if not isinstance(body, Eq):
        return False

    variables = frozenset(conjecture.variables)

    def matches_orientation(left: Expr, right: Expr) -> bool:
        env: dict[Var, Expr] = {}
        return (
            _match(conjecture.body.left, left, variables, env)
            and _match(conjecture.body.right, right, variables, env)
        )

    return matches_orientation(body.left, body.right) or matches_orientation(
        body.right,
        body.left,
    )


def subsumed_known_results(
    conjecture: ResearchConjecture,
    state: KnowledgeState,
) -> int:
    """Count existing verified results represented by this general statement."""

    return sum(
        1
        for theorem in state.theorems.values()
        if _candidate_matches_formula(conjecture, theorem.statement)
    )


def reuse_potential(
    conjecture: ResearchConjecture,
    frontier: Sequence[ResearchConjecture],
) -> int:
    """Estimate how many other frontier goals contain this candidate's structure."""

    count = 0
    for other in frontier:
        if other is conjecture or other.statement == conjecture.statement:
            continue
        body = other.body
        if (
            _contains_subexpr(body.left, conjecture.body.left)
            or _contains_subexpr(body.left, conjecture.body.right)
            or _contains_subexpr(body.right, conjecture.body.left)
            or _contains_subexpr(body.right, conjecture.body.right)
        ):
            count += 1
    return count


def assess_research_value(
    conjecture: ResearchConjecture,
    state: KnowledgeState,
    *,
    frontier: Sequence[ResearchConjecture] = (),
    min_reasoning_steps: int = 3,
    min_score: int = 14,
) -> ResearchValueAssessment:
    variable_count = len(conjecture.variables)
    primitive_steps = primitive_rewrite_distance(
        conjecture.body.left,
        conjecture.body.right,
    )
    rewrite_equivalent = primitive_steps is not None

    derivation_distance = known_derivation_distance(
        conjecture,
        state,
        max_steps=max(0, min_reasoning_steps - 1),
    )
    subsumed = subsumed_known_results(conjecture, state)
    reuse = reuse_potential(conjecture, frontier)

    kinds = _node_kinds(conjecture.body.left) | _node_kinds(
        conjecture.body.right
    )
    structural_richness = (
        len(kinds - {"var", "zero"})
        + min(4, (_expr_size(conjecture.body.left) + _expr_size(conjecture.body.right)) // 4)
    )

    # Scores are intentionally interpretable rather than learned.  They can be
    # replaced by empirical weights after Gareen accumulates benchmark data.
    generality_score = 5 * variable_count
    compression_score = min(8, 2 * subsumed + 2 * variable_count)
    reuse_score = min(10, reuse)
    novelty_score = 8 if derivation_distance is None else 0
    score = (
        generality_score
        + compression_score
        + reuse_score
        + novelty_score
        + structural_richness
    )

    accepted = True
    reason = "research-worthy candidate"

    if variable_count == 0:
        accepted = False
        reason = "ground numerical instance; keep only as conjecture evidence"
    elif rewrite_equivalent:
        accepted = False
        reason = (
            "explained entirely by primitive arithmetic rewrites"
            + (
                f" ({primitive_steps} rewrite steps)"
                if primitive_steps is not None
                else ""
            )
        )
    elif (
        derivation_distance is not None
        and derivation_distance < min_reasoning_steps
    ):
        accepted = False
        reason = (
            "too close to existing verified knowledge: "
            f"local derivation distance {derivation_distance} "
            f"< {min_reasoning_steps}"
        )
    elif score < min_score:
        accepted = False
        reason = f"research-value score {score} < threshold {min_score}"

    return ResearchValueAssessment(
        score=score,
        accepted=accepted,
        reason=reason,
        variable_count=variable_count,
        primitive_rewrite_equivalent=rewrite_equivalent,
        primitive_rewrite_steps=primitive_steps,
        known_derivation_distance=derivation_distance,
        subsumed_known_results=subsumed,
        reuse_potential=reuse,
        structural_richness=structural_richness,
    )


def rank_research_conjectures(
    conjectures: Sequence[ResearchConjecture],
    state: KnowledgeState,
    *,
    min_reasoning_steps: int = 3,
    min_score: int = 14,
) -> tuple[RankedConjecture, ...]:
    ranked = [
        RankedConjecture(
            conjecture=item,
            assessment=assess_research_value(
                item,
                state,
                frontier=conjectures,
                min_reasoning_steps=min_reasoning_steps,
                min_score=min_score,
            ),
        )
        for item in conjectures
    ]

    return tuple(
        sorted(
            ranked,
            key=lambda item: (
                0 if item.assessment.accepted else 1,
                -item.assessment.score,
                -item.assessment.reuse_potential,
                -item.assessment.variable_count,
                str(item.conjecture.statement),
            ),
        )
    )
