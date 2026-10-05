"""Generation-4 ChatGPT-designed neighbourhood campaign: 20 Melakat-selected parents x 20 children.

The 20 mutation operators were designed in the ChatGPT research loop. Gareen
performs sample filtering, research-value assessment, proof search, and formal
verification. No child is treated as true before Gareen verifies it.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path

from artificial_mathematician import ResearchConjecture, StrategySelector, InductionSynthesizer
from proof_search import BoundedProofSearcher
from math_world import X, Y, Z, W, ZERO, ONE, Add, Mul, Succ, Eq, ForAll, build_initial_knowledge, normalize, substitute_expr
from research_value import assess_research_value
from experiments.ai_parent_conjectures_100 import candidate_specs

SELECTED = [
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C01",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C02",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C03",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C04",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C05",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C06",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C07",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C08",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C09",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C10",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C11",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C12",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C13",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C14",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C15",
  "T7_ADD_COMMUTATIVE_C07_G2C04_G3C16",
  "T7_ADD_COMMUTATIVE_C07_G2C05_G3C01",
  "T7_ADD_COMMUTATIVE_C07_G2C05_G3C02",
  "T7_ADD_COMMUTATIVE_C07_G2C05_G3C03",
  "T7_ADD_COMMUTATIVE_C07_G2C05_G3C04"
]

def close_eq(left,right,variables):
    body=Eq(left,right); statement=body
    for v in reversed(variables): statement=ForAll(v,statement)
    return ResearchConjecture(statement=statement,body=body,variables=tuple(variables),heuristic_score=12+2*len(variables),evidence="Generation-4 ChatGPT-designed child of a Melakat-selected verified parent.")

def sample_signature(expr, variables):
    from itertools import product
    vals=(ZERO,ONE,Succ(ONE)); out=[]
    for combo in product(vals,repeat=len(variables)):
        g=expr
        for var,value in zip(variables,combo): g=substitute_expr(g,var,value)
        try: n,_=normalize(g,max_steps=2000); out.append(str(n))
        except RuntimeError: out.append("<normalization-failed>")
    return tuple(out)

def mutations(l,r,vars_):
    a=vars_[0] if vars_ else X
    b=vars_[1] if len(vars_)>1 else a
    # 16 truth-preserving neighbourhood/context mutations + 4 deliberate exploratory perturbations.
    return [
      (Succ(l),Succ(r)), (Add(l,ZERO),Add(r,ZERO)), (Add(ZERO,l),Add(ZERO,r)),
      (Mul(l,ONE),Mul(r,ONE)), (Mul(ONE,l),Mul(ONE,r)),
      (Add(l,ONE),Add(r,ONE)), (Add(ONE,l),Add(ONE,r)),
      (Add(l,a),Add(r,a)), (Add(a,l),Add(a,r)),
      (Mul(l,a),Mul(r,a)), (Mul(a,l),Mul(a,r)),
      (Add(Succ(l),b),Add(Succ(r),b)), (Add(b,Succ(l)),Add(b,Succ(r))),
      (Mul(Succ(l),ONE),Mul(Succ(r),ONE)),
      (Add(Add(l,a),b),Add(Add(r,a),b)),
      (Mul(Mul(l,ONE),a),Mul(Mul(r,ONE),a)),
      (Succ(l),r), (Add(l,ONE),r), (l,Succ(r)), (Mul(l,ZERO),r),
    ]

def base_specs():
    fam=candidate_specs(); out={}
    for pid in SELECTED:
        g2, g3n = pid.rsplit("_G3C",1)
        g1, g2n = g2.rsplit("_G2C",1)
        family, g1n = g1.rsplit("_C",1)
        left,right,variables=fam[family][int(g1n)-1]
        left,right=mutations(left,right,variables)[int(g2n)-1]
        left,right=mutations(left,right,variables)[int(g3n)-1]
        out[pid]=(left,right,variables)
    return out

def main():
    state=build_initial_knowledge()
    searcher=BoundedProofSearcher(max_depth=4,max_terms=24,instantiation_rounds=1,allow_open_goals=True)
    selector=StrategySelector(direct_searcher=searcher,induction=InductionSynthesizer(searcher=searcher))
    rows=[]; attempts=0
    for parent,(left,right,variables) in base_specs().items():
        children=mutations(left,right,variables)
        assert len(children)==20
        for idx,(cl,cr) in enumerate(children,1):
            q=close_eq(cl,cr,variables)
            sample=sample_signature(cl,variables)==sample_signature(cr,variables)
            assessment=assess_research_value(q,state,frontier=(),min_reasoning_steps=1)
            result=selector.solve(q,state,lemma_budget=0) if sample else None
            attempts += int(sample)
            proved=bool(result and result.found and result.check and result.check.valid)
            rows.append({"parent":parent,"index":idx,"statement":str(q.statement),"sample_pass":sample,
                         "value":assessment.score,"accepted":assessment.accepted,"reason":assessment.reason,
                         "proved":proved,"strategy":result.strategy if result else ("sample-rejected" if not sample else "unproved")})
    c=Counter()
    for r in rows:
        c["total"]+=1; c["sample_pass"]+=int(r["sample_pass"]); c["sample_fail"]+=int(not r["sample_pass"])
        c["research_accepted"]+=int(r["accepted"]); c["research_rejected"]+=int(not r["accepted"])
        c["proved"]+=int(r["proved"]); c["unproved"]+=int(not r["proved"]); c["proved_and_accepted"]+=int(r["proved"] and r["accepted"])
    print("CHATGPT_MELAKAT_GENERATION_4")
    print(f"parents={len(SELECTED)} candidates={len(rows)} children_per_parent=20 proof_attempts={attempts}")
    for k in ("total","sample_pass","sample_fail","research_accepted","research_rejected","proved","unproved","proved_and_accepted"): print(f"{k}={c[k]}")
    bp=defaultdict(Counter)
    for r in rows:
        x=bp[r["parent"]]; x["total"]+=1; x["sample_pass"]+=int(r["sample_pass"]); x["proved"]+=int(r["proved"]); x["accepted"]+=int(r["accepted"])
    print("BY_PARENT")
    for p in SELECTED: print(p,dict(bp[p]))
    batch={"source":"chatgpt-melakat-generation-4","generation":3,"parent_count":len(SELECTED),"children_per_parent":20,
           "candidates":[{"id":f'{r["parent"]}_G4C{r["index"]:02d}',"parent_id":r["parent"],"parent_ids":[r["parent"]],
             "statement":r["statement"],"generation":4,"lineage_id":r["parent"].split("_C")[0],
             "mathematical_value":r["value"],"research_accepted":r["accepted"],"proof_status":"verified",
             "value_components":{"gareen_research_value":r["value"]},"proof_strategy":r["strategy"]}
             for r in rows if r["proved"]]}
    p=Path("outputs/gareen_generation_4_verified.json"); p.parent.mkdir(exist_ok=True); p.write_text(json.dumps(batch,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"VERIFIED_BATCH_PATH={p}"); print(f"VERIFIED_BATCH_COUNT={len(batch['candidates'])}")

if __name__=="__main__": main()
