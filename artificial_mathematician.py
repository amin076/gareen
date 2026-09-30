"""Gareen Phase 11: Artificial Mathematician prototype.

The prototype coordinates conjecture generation, proof-strategy selection,
induction synthesis, lemma proposal, proof verification, and research logging.

All exploratory components are untrusted. Only math_world.check_proof and
KnowledgeState.add_theorem may admit mathematical knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from typing import Optional

from general_conjecture import (
    GeneralConjecture,
    generate_general_conjectures,
    generate_unary_expression_grammar,
)
from math_world import (
    ONE,
    THREE,
    TWO,
    X,
    Y,
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
    Var,
    check_proof,
    free_vars_expr,
    normalize,
    substitute_expr,
    substitute_formula,
    RULE_ASSUMPTION,
    RULE_FORALL_INTRO,
    RULE_INDUCTION,
)
from proof_search import (
    BoundedProofSearcher,
    SearchStats,
    compile_derivation,
)


@dataclass(frozen=True)
class ResearchConjecture:
    statement: Formula
    body: Eq
    variables: tuple[Var, ...]
    heuristic_score: int
    evidence: str


@dataclass(frozen=True)
class StrategyAttempt:
    strategy: str
    success: bool
    proof_steps: int
    reason: str = ""


@dataclass(frozen=True)
class StrategyResult:
    conjecture: ResearchConjecture
    strategy: str
    found: bool
    proof: Optional[Proof]
    check: Optional[ProofCheckResult]
    attempts: tuple[StrategyAttempt, ...]
    invented_lemmas: tuple[str, ...] = ()


@dataclass(frozen=True)
class MathematicianDiscovery:
    theorem_name: str
    statement: Formula
    strategy: str
    proof_steps: int
    dependencies: tuple[str, ...]
    invented_lemmas: tuple[str, ...]
    heuristic_score: int


@dataclass(frozen=True)
class MathematicianAttempt:
    statement: Formula
    status: str
    strategy: str
    proof_steps: int
    reason: str


@dataclass(frozen=True)
class ResearchNotebook:
    generated_conjectures: int
    attempted_conjectures: int
    accepted_theorems: int
    invented_lemmas: int
    attempts: tuple[MathematicianAttempt, ...]
    discoveries: tuple[MathematicianDiscovery, ...]


def _expr_size(expr: Expr) -> int:
    if expr == ZERO:
        return 1
    if isinstance(expr, Succ):
        return 1 + _expr_size(expr.value)
    if isinstance(expr, (Add, Mul)):
        return 1 + _expr_size(expr.left) + _expr_size(expr.right)
    return 1


def _operator_count(expr: Expr) -> int:
    if isinstance(expr, Succ):
        return 1 + _operator_count(expr.value)
    if isinstance(expr, (Add, Mul)):
        return 1 + _operator_count(expr.left) + _operator_count(expr.right)
    return 0


def _statement_complexity(statement: Formula) -> int:
    _, body = split_universal(statement)
    if isinstance(body, Eq):
        return _expr_size(body.left) + _expr_size(body.right)
    return 10_000


def split_universal(statement: Formula) -> tuple[tuple[Var, ...], Formula]:
    variables: list[Var] = []
    current = statement

    while isinstance(current, ForAll):
        variables.append(current.variable)
        current = current.body

    return tuple(variables), current


def close_universally(body: Formula, variables: tuple[Var, ...]) -> Formula:
    current = body
    for variable in reversed(variables):
        current = ForAll(variable, current)
    return current


def _canonical_equality(left: Expr, right: Expr) -> tuple[str, str]:
    a, b = str(left), str(right)
    return tuple(sorted((a, b)))


def _canonical_statement(statement: Formula) -> tuple[tuple[str, ...], tuple[str, str]] | None:
    variables, body = split_universal(statement)
    if not isinstance(body, Eq):
        return None

    replacements = (X, Y)
    if len(variables) > len(replacements):
        return None

    normalized = body
    for source, target in zip(variables, replacements):
        normalized = substitute_formula(normalized, source, target)

    if not isinstance(normalized, Eq):
        return None

    return (
        tuple(variable.name for variable in replacements[: len(variables)]),
        _canonical_equality(normalized.left, normalized.right),
    )


def _existing_statement_keys(state: KnowledgeState) -> set[tuple]:
    keys: set[tuple] = set()

    for axiom in state.world.axioms:
        key = _canonical_statement(axiom.formula)
        if key is not None:
            keys.add(key)

    for theorem in state.theorems.values():
        key = _canonical_statement(theorem.statement)
        if key is not None:
            keys.add(key)

    return keys


def _bivariate_expression_grammar() -> tuple[Expr, ...]:
    atoms: tuple[Expr, ...] = (X, Y, ZERO, ONE)
    expressions: set[Expr] = {
        X,
        Y,
        Succ(X),
        Succ(Y),
        Add(X, Y),
        Add(Y, X),
        Add(ZERO, X),
        Add(X, ZERO),
        Add(ZERO, Y),
        Add(Y, ZERO),
        Add(Succ(X), Y),
        Add(X, Succ(Y)),
        Succ(Add(X, Y)),
        Succ(Add(Y, X)),
        Mul(X, Y),
        Mul(Y, X),
        Mul(ONE, X),
        Mul(X, ONE),
        Mul(ONE, Y),
        Mul(Y, ONE),
        Add(Add(X, Y), ONE),
        Add(X, Add(Y, ONE)),
    }

    for left in atoms:
        for right in atoms:
            expressions.add(Add(left, right))
            expressions.add(Mul(left, right))

    return tuple(
        sorted(
            (
                expr
                for expr in expressions
                if X in free_vars_expr(expr) or Y in free_vars_expr(expr)
            ),
            key=lambda expr: (_expr_size(expr), str(expr)),
        )
    )


def _observe_bivariate(
    expr: Expr,
    samples: tuple[Expr, ...] = (ZERO, ONE, TWO),
) -> tuple[Expr, ...]:
    outputs: list[Expr] = []

    for x_value, y_value in product(samples, repeat=2):
        grounded = substitute_expr(expr, X, x_value)
        grounded = substitute_expr(grounded, Y, y_value)
        normal, _ = normalize(grounded)
        outputs.append(normal)

    return tuple(outputs)


def _score_conjecture(left: Expr, right: Expr, variables: int) -> int:
    score = _operator_count(left) + _operator_count(right)
    score += 2 * variables
    if type(left) is not type(right):
        score += 2
    return score


def generate_bivariate_conjectures(
    state: KnowledgeState,
) -> tuple[ResearchConjecture, ...]:
    expressions = _bivariate_expression_grammar()
    classes: dict[tuple[Expr, ...], list[Expr]] = {}

    for expr in expressions:
        classes.setdefault(_observe_bivariate(expr), []).append(expr)

    existing = _existing_statement_keys(state)
    conjectures: dict[tuple, ResearchConjecture] = {}

    for signature, group in classes.items():
        if len(group) < 2:
            continue

        for left, right in combinations(group, 2):
            vars_used = free_vars_expr(left) | free_vars_expr(right)
            if not ({X, Y} <= vars_used):
                continue

            body = Eq(left, right)
            statement = ForAll(X, ForAll(Y, body))
            key = _canonical_statement(statement)
            if key is None or key in existing:
                continue

            conjectures.setdefault(
                key,
                ResearchConjecture(
                    statement=statement,
                    body=body,
                    variables=(X, Y),
                    heuristic_score=_score_conjecture(left, right, 2),
                    evidence=(
                        "Both expressions had identical normal forms on the "
                        "3×3 sample grid over {0,1,2}."
                    ),
                ),
            )

    return tuple(
        sorted(
            conjectures.values(),
            key=lambda item: (
                _statement_complexity(item.statement),
                -item.heuristic_score,
                str(item.statement),
            ),
        )
    )


def generate_research_conjectures(
    state: KnowledgeState,
) -> tuple[ResearchConjecture, ...]:
    unary = generate_general_conjectures(
        generate_unary_expression_grammar(),
        state,
    )

    unary_items = [
        ResearchConjecture(
            statement=item.statement,
            body=item.body,
            variables=(X,),
            heuristic_score=item.heuristic_score,
            evidence="Unary expressions matched on the sample values 0,1,2,3.",
        )
        for item in unary
    ]

    combined = unary_items + list(generate_bivariate_conjectures(state))
    unique: dict[tuple, ResearchConjecture] = {}

    for item in combined:
        key = _canonical_statement(item.statement)
        if key is not None:
            unique.setdefault(key, item)

    return tuple(
        sorted(
            unique.values(),
            key=lambda item: (
                len(item.variables),
                _statement_complexity(item.statement),
                -item.heuristic_score,
                str(item.statement),
            ),
        )
    )


def _offset_step(step: ProofStep, offset: int) -> ProofStep:
    return ProofStep(
        conclusion=step.conclusion,
        rule=step.rule,
        premises=tuple(index + offset for index in step.premises),
        source=step.source,
        term=step.term,
        variable=step.variable,
        discharge=(
            step.discharge + offset
            if step.discharge is not None
            else None
        ),
        note=step.note,
    )


def _append_forall_intro(
    steps: list[ProofStep],
    current_formula: Formula,
    variables: tuple[Var, ...],
) -> Formula:
    current = current_formula

    for variable in reversed(variables):
        current = ForAll(variable, current)
        steps.append(
            ProofStep(
                conclusion=current,
                rule=RULE_FORALL_INTRO,
                premises=(len(steps) - 1,),
                variable=variable,
            )
        )

    return current


class InductionSynthesizer:
    """Build one-variable induction structure around bounded proof search."""

    def __init__(
        self,
        searcher: Optional[BoundedProofSearcher] = None,
    ) -> None:
        self.searcher = searcher or BoundedProofSearcher(
            max_depth=6,
            max_terms=40,
            instantiation_rounds=1,
            allow_open_goals=True,
        )

    def synthesize(
        self,
        conjecture: ResearchConjecture,
        state: KnowledgeState,
    ) -> Optional[Proof]:
        variables, body = split_universal(conjecture.statement)
        if not variables or not isinstance(body, Eq):
            return None

        induction_variable = variables[-1]
        parameter_variables = variables[:-1]

        base_goal = substitute_formula(
            body,
            induction_variable,
            ZERO,
        )
        step_goal = substitute_formula(
            body,
            induction_variable,
            Succ(induction_variable),
        )
        induction_hypothesis = body

        base_search = self.searcher.derive(base_goal, state)
        if base_search.root is None:
            return None

        step_search = self.searcher.derive(
            step_goal,
            state,
            assumptions=(induction_hypothesis,),
        )
        if step_search.root is None:
            return None

        base_proof = compile_derivation(base_goal, base_search.root)
        step_proof = compile_derivation(step_goal, step_search.root)

        steps = list(base_proof.steps)
        base_final = len(steps) - 1

        offset = len(steps)
        shifted_step = [
            _offset_step(step, offset)
            for step in step_proof.steps
        ]
        steps.extend(shifted_step)
        step_final = len(steps) - 1

        assumption_indices = [
            index
            for index, step in enumerate(steps)
            if (
                step.rule == RULE_ASSUMPTION
                and step.conclusion == induction_hypothesis
            )
        ]
        if len(assumption_indices) != 1:
            return None

        induction_formula = ForAll(induction_variable, body)
        steps.append(
            ProofStep(
                conclusion=induction_formula,
                rule=RULE_INDUCTION,
                premises=(base_final, step_final),
                variable=induction_variable,
                discharge=assumption_indices[0],
            )
        )

        final_formula = _append_forall_intro(
            steps,
            induction_formula,
            parameter_variables,
        )

        if final_formula != conjecture.statement:
            return None

        proof = Proof(
            statement=conjecture.statement,
            steps=tuple(steps),
        )
        check = check_proof(
            proof,
            axioms=state.world.axioms,
            known_theorems=tuple(state.theorems.values()),
        )
        return proof if check.valid else None


class LemmaProposer:
    """Suggest lower-complexity conjectures that may unlock a parent proof."""

    def propose(
        self,
        parent: ResearchConjecture,
        state: KnowledgeState,
        *,
        limit: int = 4,
    ) -> tuple[ResearchConjecture, ...]:
        parent_complexity = _statement_complexity(parent.statement)
        candidates = generate_research_conjectures(state)

        selected = [
            item
            for item in candidates
            if (
                item.statement != parent.statement
                and _statement_complexity(item.statement) < parent_complexity
            )
        ]

        return tuple(selected[:limit])


class StrategySelector:
    """Try direct proof, induction, then verified helper lemmas."""

    def __init__(
        self,
        *,
        direct_searcher: Optional[BoundedProofSearcher] = None,
        induction: Optional[InductionSynthesizer] = None,
        lemma_proposer: Optional[LemmaProposer] = None,
    ) -> None:
        self.direct_searcher = direct_searcher or BoundedProofSearcher(
            max_depth=6,
            max_terms=40,
            instantiation_rounds=1,
            allow_open_goals=True,
        )
        self.induction = induction or InductionSynthesizer()
        self.lemma_proposer = lemma_proposer or LemmaProposer()

    def _direct_proof(
        self,
        conjecture: ResearchConjecture,
        state: KnowledgeState,
    ) -> Optional[Proof]:
        variables, body = split_universal(conjecture.statement)
        result = self.direct_searcher.prove(body, state)
        if not result.found or result.proof is None:
            return None

        steps = list(result.proof.steps)
        final_formula = _append_forall_intro(
            steps,
            body,
            variables,
        )
        if final_formula != conjecture.statement:
            return None

        proof = Proof(
            statement=conjecture.statement,
            steps=tuple(steps),
        )
        check = check_proof(
            proof,
            axioms=state.world.axioms,
            known_theorems=tuple(state.theorems.values()),
        )
        return proof if check.valid else None

    def solve(
        self,
        conjecture: ResearchConjecture,
        state: KnowledgeState,
        *,
        lemma_budget: int = 2,
    ) -> StrategyResult:
        attempts: list[StrategyAttempt] = []

        direct = self._direct_proof(conjecture, state)
        attempts.append(
            StrategyAttempt(
                strategy="direct",
                success=direct is not None,
                proof_steps=len(direct.steps) if direct is not None else 0,
                reason="" if direct is not None else "Bounded direct proof search failed.",
            )
        )
        if direct is not None:
            check = check_proof(
                direct,
                axioms=state.world.axioms,
                known_theorems=tuple(state.theorems.values()),
            )
            return StrategyResult(
                conjecture=conjecture,
                strategy="direct",
                found=True,
                proof=direct,
                check=check,
                attempts=tuple(attempts),
            )

        induction_proof = self.induction.synthesize(conjecture, state)
        attempts.append(
            StrategyAttempt(
                strategy="induction",
                success=induction_proof is not None,
                proof_steps=(
                    len(induction_proof.steps)
                    if induction_proof is not None
                    else 0
                ),
                reason=(
                    ""
                    if induction_proof is not None
                    else "Automatic induction synthesis failed."
                ),
            )
        )
        if induction_proof is not None:
            check = check_proof(
                induction_proof,
                axioms=state.world.axioms,
                known_theorems=tuple(state.theorems.values()),
            )
            return StrategyResult(
                conjecture=conjecture,
                strategy="induction",
                found=True,
                proof=induction_proof,
                check=check,
                attempts=tuple(attempts),
            )

        invented: list[str] = []
        for lemma in self.lemma_proposer.propose(
            conjecture,
            state,
            limit=lemma_budget,
        ):
            lemma_direct = self._direct_proof(lemma, state)
            lemma_induction = (
                lemma_direct
                if lemma_direct is not None
                else self.induction.synthesize(lemma, state)
            )
            if lemma_induction is None:
                attempts.append(
                    StrategyAttempt(
                        strategy="lemma-proposal",
                        success=False,
                        proof_steps=0,
                        reason=f"Could not verify proposed lemma {lemma.statement}.",
                    )
                )
                continue

            lemma_name = _next_name(state, "L")
            state.add_theorem(lemma_name, lemma_induction)
            invented.append(lemma_name)
            attempts.append(
                StrategyAttempt(
                    strategy="lemma-proposal",
                    success=True,
                    proof_steps=len(lemma_induction.steps),
                    reason=f"Verified and stored helper lemma {lemma_name}.",
                )
            )

            retry_direct = self._direct_proof(conjecture, state)
            if retry_direct is not None:
                check = check_proof(
                    retry_direct,
                    axioms=state.world.axioms,
                    known_theorems=tuple(state.theorems.values()),
                )
                return StrategyResult(
                    conjecture=conjecture,
                    strategy="lemma+direct",
                    found=True,
                    proof=retry_direct,
                    check=check,
                    attempts=tuple(attempts),
                    invented_lemmas=tuple(invented),
                )

            retry_induction = self.induction.synthesize(conjecture, state)
            if retry_induction is not None:
                check = check_proof(
                    retry_induction,
                    axioms=state.world.axioms,
                    known_theorems=tuple(state.theorems.values()),
                )
                return StrategyResult(
                    conjecture=conjecture,
                    strategy="lemma+induction",
                    found=True,
                    proof=retry_induction,
                    check=check,
                    attempts=tuple(attempts),
                    invented_lemmas=tuple(invented),
                )

        return StrategyResult(
            conjecture=conjecture,
            strategy="failed",
            found=False,
            proof=None,
            check=None,
            attempts=tuple(attempts),
            invented_lemmas=tuple(invented),
        )


def _next_name(state: KnowledgeState, prefix: str) -> str:
    index = 1
    while f"{prefix}{index}_AUTO" in state.theorems:
        index += 1
    return f"{prefix}{index}_AUTO"


class ArtificialMathematician:
    """Run a bounded research campaign from axioms or an existing knowledge state."""

    def __init__(
        self,
        *,
        max_attempts: int = 10,
        max_discoveries: int = 3,
        lemma_budget: int = 2,
        selector: Optional[StrategySelector] = None,
    ) -> None:
        self.max_attempts = max_attempts
        self.max_discoveries = max_discoveries
        self.lemma_budget = lemma_budget
        self.selector = selector or StrategySelector()

    def research(
        self,
        state: Optional[KnowledgeState] = None,
    ) -> tuple[KnowledgeState, ResearchNotebook]:
        research_state = state or KnowledgeState()
        conjectures = generate_research_conjectures(research_state)

        attempts: list[MathematicianAttempt] = []
        discoveries: list[MathematicianDiscovery] = []
        lemma_count_before = len(
            [name for name in research_state.theorems if name.startswith("L")]
        )

        for conjecture in conjectures:
            if len(attempts) >= self.max_attempts:
                break
            if len(discoveries) >= self.max_discoveries:
                break

            result = self.selector.solve(
                conjecture,
                research_state,
                lemma_budget=self.lemma_budget,
            )

            if not result.found or result.proof is None:
                attempts.append(
                    MathematicianAttempt(
                        statement=conjecture.statement,
                        status="unproved",
                        strategy="failed",
                        proof_steps=0,
                        reason="; ".join(
                            attempt.reason
                            for attempt in result.attempts
                            if attempt.reason
                        ),
                    )
                )
                continue

            theorem_name = _next_name(research_state, "AM")
            theorem = research_state.add_theorem(
                theorem_name,
                result.proof,
            )

            discoveries.append(
                MathematicianDiscovery(
                    theorem_name=theorem.name,
                    statement=theorem.statement,
                    strategy=result.strategy,
                    proof_steps=len(result.proof.steps),
                    dependencies=theorem.dependencies,
                    invented_lemmas=result.invented_lemmas,
                    heuristic_score=conjecture.heuristic_score,
                )
            )
            attempts.append(
                MathematicianAttempt(
                    statement=conjecture.statement,
                    status="accepted",
                    strategy=result.strategy,
                    proof_steps=len(result.proof.steps),
                    reason=conjecture.evidence,
                )
            )

        lemma_count_after = len(
            [name for name in research_state.theorems if name.startswith("L")]
        )

        notebook = ResearchNotebook(
            generated_conjectures=len(conjectures),
            attempted_conjectures=len(attempts),
            accepted_theorems=len(discoveries),
            invented_lemmas=lemma_count_after - lemma_count_before,
            attempts=tuple(attempts),
            discoveries=tuple(discoveries),
        )
        return research_state, notebook


def phase11_demo() -> None:
    mathematician = ArtificialMathematician(
        max_attempts=8,
        max_discoveries=3,
        lemma_budget=2,
    )

    # Start from axioms only. No hand-authored T1-T14 theorem library is loaded.
    state, notebook = mathematician.research(KnowledgeState())

    print("Gareen Phase 11 — Artificial Mathematician")
    print("===========================================")
    print("Generated conjectures:", notebook.generated_conjectures)
    print("Attempted conjectures:", notebook.attempted_conjectures)
    print("Accepted theorems:", notebook.accepted_theorems)
    print("Invented helper lemmas:", notebook.invented_lemmas)

    print("\nDiscoveries:")
    for discovery in notebook.discoveries:
        print(
            f"  - {discovery.theorem_name}: {discovery.statement} "
            f"[strategy={discovery.strategy}, steps={discovery.proof_steps}]"
        )
        if discovery.invented_lemmas:
            print("    invented lemmas:", ", ".join(discovery.invented_lemmas))
        print(
            "    dependencies:",
            ", ".join(discovery.dependencies) or "(axioms only)",
        )

    print("\nResearch notebook:")
    for attempt in notebook.attempts:
        print(
            f"  - {attempt.status}: {attempt.statement} "
            f"[strategy={attempt.strategy}, steps={attempt.proof_steps}]"
        )


if __name__ == "__main__":
    phase11_demo()
