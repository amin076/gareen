import Mathlib

open Lean Meta Elab Tactic

namespace Gareen.ProofStateProbe

structure LocalFact where
  name : String
  type : String
  deriving ToJson

structure GoalState where
  index : Nat
  target : String
  locals : Array LocalFact := #[]
  deriving ToJson

private def captureGoal (index : Nat) (g : MVarId) : MetaM GoalState :=
  g.withContext do
    let target ← ppExpr (← instantiateMVars (← g.getType))
    let mut locals : Array LocalFact := #[]
    for decl in ← getLCtx do
      if decl.isImplementationDetail then
        continue
      try
        let ty ← instantiateMVars (← inferType decl.toExpr)
        locals := locals.push {
          name := decl.userName.toString
          type := (← ppExpr ty).pretty
        }
      catch _ =>
        pure ()
    return {
      index := index
      target := target.pretty
      locals := locals
    }

/- Execute a tactic sequence, then emit every resulting Lean proof state. -/
syntax (name := gareenProbe) "gareen_probe " tacticSeq : tactic

elab_rules : tactic
  | `(tactic| gareen_probe $seq:tacticSeq) => do
      evalTactic seq
      let goals ← getGoals
      for i in [:goals.size] do
        let state ← captureGoal i goals[i]!
        logInfo m!"GAREEN_PROOF_STATE {toJson state |>.compress}"

end Gareen.ProofStateProbe
