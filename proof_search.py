"""Gareen Phase 8: bounded automatic proof search.

This module is intentionally separate from math_world.py.

The trusted proof checker remains the authority. The searcher only proposes a
proof. A candidate is accepted only if math_world.check_proof verifies every
generated proof step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from math_world import (
    ADD_SUCC,
    ADD_ZERO,
    AXIOMS,
    ONE,
    THREE,
    TWO,
    ZERO,
    Add,
    Eq,
    Expr,
    ForAll,
    Formula,
    KnowledgeState,
    Mul,
    Proof,
    ProofCheckResult,
    ProofStep,
    Succ,
    Theorem,
    Var,
    check_proof,
    free_vars_expr,
    is_free_for,
    substitute_formula,
    RULE_AXIOM,
    RULE_EQ_ADD_LEFT_CONGRUENCE,
    RULE_EQ_ADD_RIGHT_CONGRUENCE,
    RULE_EQ_MUL_LEFT_CONGRUENCE,
    RULE_EQ_MUL_RIGHT_CONGRUENCE,
    RULE_EQ_SUCC_CONGRUENCE,
    RULE_EQ_SYMMETRY,
    RULE_EQ_TRANSITIVITY,
    RULE_FORALL_ELIM,
    RULE_THEOREM,
)


@dataclass(frozen=True)
class Derivation:
    """A proof tree proposed by the untrusted search layer."""

    conclusion: Formula
    rule: str
    premises: tuple["Derivation", ...] = ()
    source: Optional[str] = None
    term: Optional[Expr] = None


@dataclass(frozen=True)
class SearchStats:
    instantiation_rounds: int
    term_count: int
    direct_fact_count: int
    equality_calls: int


@dataclass(frozen=True)
class SearchResult:
    goal: Formula
    found: bool
    proof: Optional[Proof]
    check: Optional[ProofCheckResult]
    stats: SearchStats


def _expr_size(expr: Expr) -> int:
    if isinstance(expr, (Var, type(ZERO))):
        return 1
    if isinstance(expr, Succ):
        return 1 + _expr_size(expr.value)
    if isinstance(expr, (Add, Mul)):
        return 1 + _expr_size(expr.left) + _expr_size(expr.right)
    raise TypeError(f"Unsupported expression type: {type(expr)!r}")


def _subterms(expr: Expr) -> set[Expr]:
    result = {expr}
    if isinstance(expr, Succ):
        result |= _subterms(expr.value)
    elif isinstance(expr, (Add, Mul)):
        result |= _subterms(expr.left)
        result |= _subterms(expr.right)
    return result


def _formula_terms(formula: Formula) -> set[Expr]:
    if isinstance(formula, Eq):
        return _subterms(formula.left) | _subterms(formula.right)
    if isinstance(formula, ForAll):
        return _formula_terms(formula.body)
    return set()


def _is_ground(expr: Expr) -> bool:
    return not free_vars_expr(expr)


def _compile_derivation(goal: Formula, root: Derivation) -> Proof:
    steps: list[ProofStep] = []

    def emit(node: Derivation) -> int:
        premise_indices = tuple(emit(premise) for premise in node.premises)
        index = len(steps)
        steps.append(
            ProofStep(
                conclusion=node.conclusion,
                rule=node.rule,
                premises=premise_indices,
                source=node.source,
                term=node.term,
            )
        )
        return index

    final_index = emit(root)
    if final_index != len(steps) - 1:
        raise RuntimeError("Proof compilation did not end at the root")

    return Proof(statement=goal, steps=tuple(steps))


class BoundedProofSearcher:
    """Small deterministic proof search for closed formulas.

    Phase 8 deliberately does not search induction proofs. It searches finite
    ground goals by instantiating existing universal axioms/theorems and then
    composing equality rules already trusted by the checker.
    """

    def __init__(
        self,
        *,
        max_depth: int = 5,
        max_terms: int = 48,
        instantiation_rounds: int = 2,
        max_direct_facts: int = 5000,
    ) -> None:
        self.max_depth = max_depth
        self.max_terms = max_terms
        self.instantiation_rounds = instantiation_rounds
        self.max_direct_facts = max_direct_facts

        self._direct: dict[Formula, Derivation] = {}
        self._candidate_terms: tuple[Expr, ...] = ()
        self._equality_calls = 0
        self._memo: dict[tuple[Expr, Expr, int], Optional[Derivation]] = {}

    def prove(self, goal: Formula, state: KnowledgeState) -> SearchResult:
        goal_terms = _formula_terms(goal)
        if any(not _is_ground(term) for term in goal_terms):
            raise ValueError(
                "Phase 8 search currently accepts only closed/ground goals"
            )

        terms = {
            ZERO,
            ONE,
            TWO,
            THREE,
            *goal_terms,
        }

        self._direct = {}
        self._memo = {}
        self._equality_calls = 0

        rounds_used = 0
        for round_index in range(self.instantiation_rounds):
            rounds_used = round_index + 1
            ordered_terms = self._ordered_terms(terms)
            self._instantiate_sources(
                AXIOMS,
                tuple(state.theorems.values()),
                ordered_terms,
            )

            expanded = set(terms)
            for formula in self._direct:
                expanded |= {
                    term
                    for term in _formula_terms(formula)
                    if _is_ground(term)
                }

            ordered_expanded = self._ordered_terms(expanded)
            terms = set(ordered_expanded[: self.max_terms])

            if len(terms) == len(ordered_terms) and all(
                term in terms for term in ordered_terms
            ):
                break

        self._candidate_terms = tuple(self._ordered_terms(terms))

        root = self._direct.get(goal)
        if root is None and isinstance(goal, Eq):
            root = self._prove_equality(
                goal.left,
                goal.right,
                self.max_depth,
                frozenset(),
            )

        if root is None:
            return SearchResult(
                goal=goal,
                found=False,
                proof=None,
                check=None,
                stats=self._stats(rounds_used),
            )

        proof = _compile_derivation(goal, root)
        check = check_proof(
            proof,
            axioms=state.world.axioms,
            known_theorems=tuple(state.theorems.values()),
        )

        return SearchResult(
            goal=goal,
            found=check.valid,
            proof=proof if check.valid else None,
            check=check,
            stats=self._stats(rounds_used),
        )

    def prove_and_add(
        self,
        state: KnowledgeState,
        name: str,
        goal: Formula,
    ) -> Theorem:
        result = self.prove(goal, state)
        if not result.found or result.proof is None:
            details = ""
            if result.check is not None and result.check.errors:
                details = ": " + "; ".join(result.check.errors)
            raise ValueError(f"Automatic proof search failed{details}")
        return state.add_theorem(name, result.proof)

    def _stats(self, rounds_used: int) -> SearchStats:
        return SearchStats(
            instantiation_rounds=rounds_used,
            term_count=len(self._candidate_terms),
            direct_fact_count=len(self._direct),
            equality_calls=self._equality_calls,
        )

    def _ordered_terms(self, terms: Iterable[Expr]) -> list[Expr]:
        return sorted(
            set(terms),
            key=lambda term: (_expr_size(term), str(term)),
        )[: self.max_terms]

    def _remember(self, derivation: Derivation) -> None:
        if len(self._direct) >= self.max_direct_facts:
            return
        self._direct.setdefault(derivation.conclusion, derivation)

    def _instantiate_sources(
        self,
        axioms,
        theorems: tuple[Theorem, ...],
        terms: list[Expr],
    ) -> None:
        for axiom in axioms:
            root = Derivation(
                conclusion=axiom.formula,
                rule=RULE_AXIOM,
                source=axiom.name,
            )
            self._expand_universals(root, terms)

        for theorem in theorems:
            root = Derivation(
                conclusion=theorem.statement,
                rule=RULE_THEOREM,
                source=theorem.name,
            )
            self._expand_universals(root, terms)

    def _expand_universals(
        self,
        root: Derivation,
        terms: list[Expr],
    ) -> None:
        stack = [root]

        while stack and len(self._direct) < self.max_direct_facts:
            current = stack.pop()
            formula = current.conclusion

            if not isinstance(formula, ForAll):
                self._remember(current)
                continue

            for term in reversed(terms):
                if not is_free_for(term, formula.variable, formula.body):
                    continue
                instantiated = substitute_formula(
                    formula.body,
                    formula.variable,
                    term,
                )
                stack.append(
                    Derivation(
                        conclusion=instantiated,
                        rule=RULE_FORALL_ELIM,
                        premises=(current,),
                        term=term,
                    )
                )

    def _direct_equality(
        self,
        left: Expr,
        right: Expr,
    ) -> Optional[Derivation]:
        direct = self._direct.get(Eq(left, right))
        if direct is not None:
            return direct

        reverse = self._direct.get(Eq(right, left))
        if reverse is not None:
            return Derivation(
                conclusion=Eq(left, right),
                rule=RULE_EQ_SYMMETRY,
                premises=(reverse,),
            )

        return None

    def _prove_equality(
        self,
        left: Expr,
        right: Expr,
        depth: int,
        visiting: frozenset[tuple[Expr, Expr]],
    ) -> Optional[Derivation]:
        self._equality_calls += 1

        if depth < 0:
            return None

        pair = (left, right)
        if pair in visiting:
            return None

        memo_key = (left, right, depth)
        if memo_key in self._memo:
            return self._memo[memo_key]

        direct = self._direct_equality(left, right)
        if direct is not None:
            self._memo[memo_key] = direct
            return direct

        next_visiting = visiting | {pair}

        structural = self._prove_structural(
            left,
            right,
            depth,
            next_visiting,
        )
        if structural is not None:
            self._memo[memo_key] = structural
            return structural

        if depth == 0:
            self._memo[memo_key] = None
            return None

        # Prefer terms that appear in direct equality facts touching either side.
        mids = self._rank_intermediate_terms(left, right)
        for middle in mids:
            if middle == left or middle == right:
                continue

            first = self._prove_equality(
                left,
                middle,
                depth - 1,
                next_visiting,
            )
            if first is None:
                continue

            second = self._prove_equality(
                middle,
                right,
                depth - 1,
                next_visiting,
            )
            if second is None:
                continue

            result = Derivation(
                conclusion=Eq(left, right),
                rule=RULE_EQ_TRANSITIVITY,
                premises=(first, second),
            )
            self._memo[memo_key] = result
            return result

        self._memo[memo_key] = None
        return None

    def _prove_structural(
        self,
        left: Expr,
        right: Expr,
        depth: int,
        visiting: frozenset[tuple[Expr, Expr]],
    ) -> Optional[Derivation]:
        if isinstance(left, Succ) and isinstance(right, Succ):
            inner = self._prove_equality(
                left.value,
                right.value,
                depth - 1,
                visiting,
            )
            if inner is not None:
                return Derivation(
                    conclusion=Eq(left, right),
                    rule=RULE_EQ_SUCC_CONGRUENCE,
                    premises=(inner,),
                )

        if isinstance(left, Add) and isinstance(right, Add):
            if left.right == right.right:
                premise = self._prove_equality(
                    left.left,
                    right.left,
                    depth - 1,
                    visiting,
                )
                if premise is not None:
                    return Derivation(
                        conclusion=Eq(left, right),
                        rule=RULE_EQ_ADD_LEFT_CONGRUENCE,
                        premises=(premise,),
                        term=left.right,
                    )

            if left.left == right.left:
                premise = self._prove_equality(
                    left.right,
                    right.right,
                    depth - 1,
                    visiting,
                )
                if premise is not None:
                    return Derivation(
                        conclusion=Eq(left, right),
                        rule=RULE_EQ_ADD_RIGHT_CONGRUENCE,
                        premises=(premise,),
                        term=left.left,
                    )

            # If both arguments differ, change one argument at a time.
            middle = Add(right.left, left.right)
            first = self._prove_equality(
                left,
                middle,
                depth - 1,
                visiting,
            )
            if first is not None:
                second = self._prove_equality(
                    middle,
                    right,
                    depth - 1,
                    visiting,
                )
                if second is not None:
                    return Derivation(
                        conclusion=Eq(left, right),
                        rule=RULE_EQ_TRANSITIVITY,
                        premises=(first, second),
                    )

        if isinstance(left, Mul) and isinstance(right, Mul):
            if left.right == right.right:
                premise = self._prove_equality(
                    left.left,
                    right.left,
                    depth - 1,
                    visiting,
                )
                if premise is not None:
                    return Derivation(
                        conclusion=Eq(left, right),
                        rule=RULE_EQ_MUL_LEFT_CONGRUENCE,
                        premises=(premise,),
                        term=left.right,
                    )

            if left.left == right.left:
                premise = self._prove_equality(
                    left.right,
                    right.right,
                    depth - 1,
                    visiting,
                )
                if premise is not None:
                    return Derivation(
                        conclusion=Eq(left, right),
                        rule=RULE_EQ_MUL_RIGHT_CONGRUENCE,
                        premises=(premise,),
                        term=left.left,
                    )

            middle = Mul(right.left, left.right)
            first = self._prove_equality(
                left,
                middle,
                depth - 1,
                visiting,
            )
            if first is not None:
                second = self._prove_equality(
                    middle,
                    right,
                    depth - 1,
                    visiting,
                )
                if second is not None:
                    return Derivation(
                        conclusion=Eq(left, right),
                        rule=RULE_EQ_TRANSITIVITY,
                        premises=(first, second),
                    )

        return None

    def _rank_intermediate_terms(
        self,
        left: Expr,
        right: Expr,
    ) -> tuple[Expr, ...]:
        touched: set[Expr] = set()

        for formula in self._direct:
            if not isinstance(formula, Eq):
                continue
            if formula.left in (left, right) or formula.right in (left, right):
                touched.add(formula.left)
                touched.add(formula.right)

        remaining = [
            term
            for term in self._candidate_terms
            if term not in touched
        ]

        ordered_touched = sorted(
            touched,
            key=lambda term: (_expr_size(term), str(term)),
        )
        return tuple(ordered_touched + remaining)


def phase8_demo() -> None:
    """Let Gareen construct a proof that was not hand-authored."""

    state = __import__("math_world").build_initial_knowledge()
    searcher = BoundedProofSearcher(max_depth=5)

    goal = Eq(Add(TWO, ONE), THREE)
    result = searcher.prove(goal, state)

    print("Gareen Phase 8")
    print("================")
    print("Goal:", goal)
    print("Found:", result.found)
    print("Stats:", result.stats)

    if result.proof is not None:
        print("\nAutomatically constructed proof:")
        for index, step in enumerate(result.proof.steps):
            print(f"{index:>2}. {step.rule}: {step.conclusion}")

        theorem = state.add_theorem("AUTO_TWO_PLUS_ONE", result.proof)
        print("\nAccepted theorem:", theorem)


if __name__ == "__main__":
    phase8_demo()
