import Mathlib
import Lean.Meta.Tactic.LibrarySearch

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

structure DecompositionState where
  rule : String
  goals : Array GoalState := #[]
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
      let mut index := 0
      let mut report := ""
      for goal in goals do
        let state ← captureGoal index goal
        report := report ++ s!"GAREEN_PROOF_STATE {toJson state |>.compress}\n"
        index := index + 1
      throwError s!"GAREEN_PROBE_COUNT {goals.length}\n{report}"

private def labelRule (name : Name) (mod : LibrarySearch.DeclMod) : String :=
  name.toString ++ match mod with
    | .none => ""
    | .mp => ".mp"
    | .mpr => ".mpr"

/-- Ask Lean itself for a useful decomposition. Constructors and indexed
library-search declarations are tried transactionally. Gareen does not inspect
the target syntax to decide how it should split; the emitted child proof states
are the actual metavariable goals produced by Lean. -/
syntax (name := gareenProbeAuto) "gareen_probe_auto" : tactic

elab_rules : tactic
  | `(tactic| gareen_probe_auto) => do
      let goal ← getMainGoal
      let before ← saveState
      let base ← getMCtx
      let type ← goal.withContext do instantiateMVars (← goal.getType)
      let constructors : Array (Name × LibrarySearch.DeclMod) :=
        match (← getEnv).find? (type.getAppFn.constName?.getD .anonymous) with
        | some (.inductInfo info) =>
            info.ctors.toArray.map (fun n => (n, .none))
        | _ => #[]

      let mut chosenRule : Option String := none
      let mut chosenGoals : List MVarId := []
      let mut chosenState : Option MetavarContext := none

      -- First ask the target type itself how it decomposes.  This is generic
      -- (And.intro, Exists.intro, structure constructors, etc.) and avoids an
      -- expensive global library search when the local inductive structure is
      -- already sufficient.
      for (name, mod) in constructors do
        if chosenRule.isNone then
          setMCtx base
          try
            let lemmaExpr ← goal.withContext do LibrarySearch.mkLibrarySearchLemma name mod
            let children ← goal.apply lemmaExpr
            let mut remaining : List MVarId := []
            for child in children do
              if !(← child.isAssigned) then
                remaining := remaining.concat child
            if remaining.length >= 2 then
              chosenRule := some (labelRule name mod)
              chosenGoals := remaining
              chosenState := some (← getMCtx)
          catch _ =>
            pure ()

      -- Only if the target constructor did not expose a useful split, consult
      -- a small bounded set of indexed library declarations.
      if chosenRule.isNone then
        setMCtx base
        let indexed ← goal.withContext do LibrarySearch.libSearchFindDecls type
        for (name, mod) in indexed.toList.take 24 do
          if chosenRule.isNone then
            setMCtx base
            try
              let lemmaExpr ← goal.withContext do LibrarySearch.mkLibrarySearchLemma name mod
              let children ← goal.apply lemmaExpr
              let mut remaining : List MVarId := []
              for child in children do
                if !(← child.isAssigned) then
                  remaining := remaining.concat child
              if remaining.length >= 2 then
                chosenRule := some (labelRule name mod)
                chosenGoals := remaining
                chosenState := some (← getMCtx)
            catch _ =>
              pure ()

      match chosenRule, chosenState with
      | some rule, some state =>
          setMCtx state
          let mut reports : Array GoalState := #[]
          for i in [:chosenGoals.length] do
            reports := reports.push (← captureGoal i chosenGoals[i]!)
          logInfo m!"GAREEN_DECOMPOSITION_RULE {rule}"
          for report in reports do
            logInfo m!"GAREEN_PROOF_STATE {toJson report |>.compress}"
          replaceMainGoal chosenGoals
          throwError s!"GAREEN_PROBE_COUNT {chosenGoals.length}"
      | _, _ =>
          before.restore
          throwError "GAREEN_NO_DYNAMIC_DECOMPOSITION"

end Gareen.ProofStateProbe
