import Mathlib
import Lean.Meta.Tactic.LibrarySearch

/-! Bounded, ranked backward search. All applications and substitutions are performed by
Lean's elaborator. Failed branches restore their entire metavariable context. No domain
lemma names or arithmetic decomposition templates occur in this module. -/
open Lean Meta Elab Tactic

namespace Gareen.RecursivePlanner

structure Config where
  maxDepth : Nat := 6
  maxNodes : Nat := 600
  maxCandidates : Nat := 48
  preferred : Array Name := #[]

structure Event where
  id : Nat
  parent : Nat
  goal : String
  rule : String
  status : String
  children : Array String := #[]
  deriving ToJson

structure Stats where
  nodes : Nat := 0
  events : Array Event := #[]

structure Task where
  goal : MVarId
  depth : Nat
  parent : Nat
  ancestors : List Expr := []

structure Choice where
  rule : String
  goals : List MVarId
  state : MetavarContext
  score : Nat

private def emit (stats : IO.Ref Stats) (parent : Nat) (goal rule status : String)
    (children : Array String := #[]) : MetaM Nat := do
  let s ← stats.get
  let id := s.events.size + 1
  stats.set { s with events := s.events.push { id, parent, goal, rule, status, children } }
  return id

private def label (g : MVarId) : MetaM String := g.withContext do
  return (← ppExpr (← instantiateMVars (← g.getType))).pretty

/-- Search the whole pending agenda under each choice: a later sibling can force
backtracking into an earlier sibling, including shared implicit witnesses. -/
private partial def search (cfg : Config) (stats : IO.Ref Stats)
    (pending : List Task) : MetaM Bool := do
  match pending with
  | [] => return true
  | task :: rest =>
    if ← task.goal.isAssigned then return ← search cfg stats rest
    if (← stats.get).nodes >= cfg.maxNodes then return false
    stats.modify fun s => { s with nodes := s.nodes + 1 }
    let (_, goal) ← task.goal.intros
    goal.withContext do
      let type ← instantiateMVars (← goal.getType)
      let text ← label goal
      if task.ancestors.contains type then
        let _ ← emit stats task.parent text "" "cycle"
        return false
      let base ← getMCtx
      -- Local assumptions are candidates too; their conclusions need not be ground.
      let mut choices : Array Choice := #[]
      for decl in ← getLCtx do
        if decl.isImplementationDetail then continue
        try
          let goals ← goal.apply decl.toExpr
          choices := choices.push { rule := decl.userName.toString, goals,
            state := ← getMCtx, score := goals.length }
        catch _ => pure ()
        setMCtx base
      try
        goal.refl
        choices := choices.push { rule := "rfl", goals := [], state := ← getMCtx, score := 0 }
      catch _ => pure ()
      setMCtx base
      if task.depth < cfg.maxDepth then
        let candidates ← LibrarySearch.libSearchFindDecls type
        let candidates := candidates.qsort fun a b =>
          (if cfg.preferred.contains a.1 then 0 else 1) <
          (if cfg.preferred.contains b.1 then 0 else 1)
        for (name, mod) in candidates.toList.take cfg.maxCandidates do
          if (← stats.get).nodes >= cfg.maxNodes then break
          stats.modify fun s => { s with nodes := s.nodes + 1 }
          try
            let lemma ← LibrarySearch.mkLibrarySearchLemma name mod
            let goals ← goal.apply lemma
            let mut cost := goals.length * 10
            for g in goals do
              if !(← g.withContext (isProp (← g.getType))) then cost := cost + 100
            if cfg.preferred.contains name then cost := cost / 2
            let suffix := match mod with | .none => "" | .mp => ".mp" | .mpr => ".mpr"
            choices := choices.push { rule := name.toString ++ suffix, goals,
              state := ← getMCtx, score := cost }
          catch _ => pure ()
          setMCtx base
      let choices := choices.qsort fun a b => a.score < b.score
      for choice in choices do
        setMCtx choice.state
        let children ← choice.goals.toArray.mapM label
        let id ← emit stats task.parent text choice.rule "try" children
        let next := choice.goals.map fun g =>
          { goal := g, depth := task.depth + 1, parent := id,
            ancestors := type :: task.ancestors : Task }
        if ← search cfg stats (next ++ rest) then
          let _ ← emit stats id text choice.rule "accepted"
          return true
        let _ ← emit stats id text choice.rule "backtrack"
        setMCtx base
      let _ ← emit stats task.parent text "" "unproved"
      return false

syntax (name := gareenSearch) "gareen_search" num num num (" [" ident,* "]")? : tactic

elab_rules : tactic
  | `(tactic| gareen_search $depth:num $nodes:num $width:num $[[$names:ident,*]]?) => do
    let goal ← getMainGoal
    let before ← saveState
    let stats ← IO.mkRef ({} : Stats)
    let preferred := (names.map (·.getElems.map (·.getId))).getD #[]
    let cfg : Config := { maxDepth := depth.getNat, maxNodes := nodes.getNat,
      maxCandidates := width.getNat, preferred }
    let success ← search cfg stats [{ goal, depth := 0, parent := 0 }]
    let data ← stats.get
    for event in data.events do
      logInfo m!"GAREEN_EVENT {toJson event |>.compress}"
    logInfo m!"GAREEN_NODES {data.nodes}"
    if !success then
      before.restore
      throwError "Gareen bounded recursive search exhausted; goal is unproved, not false"
    let proof ← instantiateMVars (mkMVar goal)
    if proof.hasMVar || proof.hasSorry then
      before.restore
      throwError "Gareen refuses incomplete or sorry-containing proof"
    logInfo m!"GAREEN_PROOF {← ppExpr proof}"
    replaceMainGoal []

end Gareen.RecursivePlanner
