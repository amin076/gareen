"""Research Agent v1: one autonomous generation-5 -> generation-6 cycle.

OpenAI proposes conjectures only. Gareen independently samples, scores, proves and
kernel-checks them. Only verified results are written for Melakat.
"""
from __future__ import annotations
import json, os, re, sys, time, urllib.request, urllib.error
from collections import Counter
from pathlib import Path

from artificial_mathematician import ResearchConjecture, StrategySelector, InductionSynthesizer
from proof_search import BoundedProofSearcher
from math_world import X,Y,Z,W,ZERO,ONE,Add,Mul,Succ,Eq,ForAll,build_initial_knowledge,normalize,substitute_expr
from research_value import assess_research_value

MODEL=os.environ.get("OPENAI_RESEARCH_MODEL","gpt-5.6-luna")
API_URL="https://api.openai.com/v1/responses"
CHILDREN=int(os.environ.get("CHILDREN_PER_PARENT","20"))

PARENTS=[
"T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C01","T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C02",
"T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C03","T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C04",
"T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C05","T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C06",
"T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C07","T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C08",
"T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C09","T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C10",
"T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C11","T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C12",
"T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C13","T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C14",
"T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C15","T7_ADD_COMMUTATIVE_C07_G2C04_G3C01_G4C16",
"T7_ADD_COMMUTATIVE_C07_G2C04_G3C02_G4C01","T7_ADD_COMMUTATIVE_C07_G2C04_G3C02_G4C02",
"T7_ADD_COMMUTATIVE_C07_G2C04_G3C02_G4C03","T7_ADD_COMMUTATIVE_C07_G2C04_G3C02_G4C04"]

def mutations(l,r,vs):
    a=vs[0] if vs else X; b=vs[1] if len(vs)>1 else a
    return [(Succ(l),Succ(r)),(Add(l,ZERO),Add(r,ZERO)),(Add(ZERO,l),Add(ZERO,r)),
      (Mul(l,ONE),Mul(r,ONE)),(Mul(ONE,l),Mul(ONE,r)),(Add(l,ONE),Add(r,ONE)),
      (Add(ONE,l),Add(ONE,r)),(Add(l,a),Add(r,a)),(Add(a,l),Add(a,r)),
      (Mul(l,a),Mul(r,a)),(Mul(a,l),Mul(a,r)),(Add(Succ(l),b),Add(Succ(r),b)),
      (Add(b,Succ(l)),Add(b,Succ(r)),(Mul(Succ(l),ONE),Mul(Succ(r),ONE)),
      (Add(Add(l,a),b),Add(Add(r,a),b)),(Mul(Mul(l,ONE),a),Mul(Mul(r,ONE),a)),
      (Succ(l),r),(Add(l,ONE),r),(l,Succ(r)),(Mul(l,ZERO),r)]

def parent_specs():
    from experiments.ai_parent_conjectures_100 import candidate_specs
    fam=candidate_specs(); out={}
    for pid in PARENTS:
        g3,g4n=pid.rsplit("_G4C",1); g2,g3n=g3.rsplit("_G3C",1); g1,g2n=g2.rsplit("_G2C",1)
        family,g1n=g1.rsplit("_C",1)
        l,r,vs=fam[family][int(g1n)-1]
        for n in (g2n,g3n,g4n): l,r=mutations(l,r,vs)[int(n)-1]
        out[pid]=(l,r,vs)
    return out

TOK=re.compile(r"\s*(Add|Mul|S|0|x|y|z|w|\(|\)|,)")
V={"x":X,"y":Y,"z":Z,"w":W}
def parse_expr(s):
    toks=TOK.findall(s); pos=0
    def p():
        nonlocal pos
        if pos>=len(toks): raise ValueError("unexpected end")
        t=toks[pos]; pos+=1
        if t=="0": return ZERO
        if t in V: return V[t]
        if t=="S":
            assert toks[pos]=="("; pos+=1; a=p(); assert toks[pos]==")"; pos+=1; return Succ(a)
        if t in ("Add","Mul"):
            assert toks[pos]=="("; pos+=1; a=p(); assert toks[pos]==","; pos+=1; b=p(); assert toks[pos]==")"; pos+=1
            return Add(a,b) if t=="Add" else Mul(a,b)
        raise ValueError(t)
    e=p()
    if pos!=len(toks) or "".join(toks).replace(" ","")!=re.sub(r"\s+","",s): raise ValueError("invalid syntax")
    return e

def close_eq(l,r,vs):
    body=Eq(l,r); st=body
    for v in reversed(vs): st=ForAll(v,st)
    return ResearchConjecture(statement=st,body=body,variables=tuple(vs),heuristic_score=20,
      evidence="OpenAI Research Agent v1 conjecture; untrusted until Gareen verification.")

def sample_signature(e,vs):
    from itertools import product
    vals=(ZERO,ONE,Succ(ONE)); out=[]
    for combo in product(vals,repeat=len(vs)):
        g=e
        for v,val in zip(vs,combo): g=substitute_expr(g,v,val)
        try: n,_=normalize(g,max_steps=2000); out.append(str(n))
        except RuntimeError: out.append("<fail>")
    return tuple(out)

def response_text(body):
    return "\n".join(c.get("text","") for i in body.get("output",[]) if i.get("type")=="message"
      for c in i.get("content",[]) if c.get("type")=="output_text").strip()

def call_ai(key,pid,l,r,vs):
    prompt=f"""You are the creative conjecture generator in Gareen Research Agent v1.
Parent ID: {pid}
Verified parent: {close_eq(l,r,vs).statement}
Generate exactly {CHILDREN} DISTINCT candidate equalities in the mathematical neighbourhood.
Explore genuinely different research moves: generalization, strengthening, converse-like ideas,
variable rearrangement, abstraction, consequences, and structural combinations. Some candidates
may be false. Do NOT claim proof or truth.
Allowed expression grammar ONLY: 0 | x | y | z | w | S(expr) | Add(expr,expr) | Mul(expr,expr).
Use variables only from {[str(v) for v in vs]}.
Return JSON only: {{"candidates":[{{"left":"...","right":"...","idea":"short label"}}, ...]}}.
Avoid merely wrapping both sides with the same S/Add/Mul context whenever possible."""
    payload={"model":MODEL,"input":prompt,"max_output_tokens":5000}
    req=urllib.request.Request(API_URL,data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=120) as resp: body=json.loads(resp.read())
    text=response_text(body); text=re.sub(r"^\s*```(?:json)?|\s*```\s*$","",text,flags=re.I|re.S)
    data=json.loads(text); usage=body.get("usage",{})
    return data["candidates"],usage,body.get("id","unknown")

def main():
    key=os.environ.get("OPENAI_API_KEY")
    if not key: raise SystemExit("OPENAI_API_KEY missing")
    specs=parent_specs(); raw=[]; usage=Counter(); calls=0
    for pid,(l,r,vs) in specs.items():
        try:
            children,u,rid=call_ai(key,pid,l,r,vs); calls+=1
        except Exception as e:
            print(f"AI_CALL_FAILED parent={pid} error={type(e).__name__}:{e}"); continue
        for k in ("input_tokens","output_tokens","total_tokens"): usage[k]+=int(u.get(k,0) or 0)
        valid=0
        for c in children:
            try:
                cl,cr=parse_expr(c["left"]),parse_expr(c["right"])
                raw.append((pid,cl,cr,vs,str(c.get("idea",""))[:120],rid)); valid+=1
            except Exception as e: print(f"AI_CHILD_REJECTED parent={pid} error={type(e).__name__}")
        print(f"AI_PARENT_OK parent={pid} returned={len(children)} valid={valid} response_id={rid}")
    # exact structural dedup while preserving provenance
    seen=set(); uniq=[]
    for row in raw:
        key2=(str(row[1]),str(row[2]),tuple(map(str,row[3])))
        if key2 not in seen: seen.add(key2); uniq.append(row)
    state=build_initial_knowledge()
    searcher=BoundedProofSearcher(max_depth=4,max_terms=24,instantiation_rounds=1,allow_open_goals=True)
    selector=StrategySelector(direct_searcher=searcher,induction=InductionSynthesizer(searcher=searcher))
    rows=[]
    for idx,(pid,l,r,vs,idea,rid) in enumerate(uniq,1):
        q=close_eq(l,r,vs); sample=sample_signature(l,vs)==sample_signature(r,vs)
        a=assess_research_value(q,state,frontier=(),min_reasoning_steps=1)
        result=selector.solve(q,state,lemma_budget=0) if sample else None
        proved=bool(result and result.found and result.check and result.check.valid)
        rows.append({"id":f"RA5_{idx:04d}","parent_id":pid,"statement":str(q.statement),"sample":sample,
          "value":a.score,"accepted":a.accepted,"proved":proved,"strategy":result.strategy if result else ("sample-rejected" if not sample else "unproved"),
          "idea":idea,"openai_response_id":rid})
    verified=[{"id":r["id"],"parent_id":r["parent_id"],"parent_ids":[r["parent_id"]],"statement":r["statement"],
      "generation":5,"lineage_id":r["parent_id"].split("_C")[0],"mathematical_value":r["value"],
      "research_accepted":r["accepted"],"proof_status":"verified","value_components":{"gareen_research_value":r["value"]},
      "proof_strategy":r["strategy"],"idea":r["idea"]} for r in rows if r["proved"]]
    batch={"source":"gareen-research-agent-v1","generation":5,"parent_count":len(PARENTS),"model":MODEL,"candidates":verified}
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/research_agent_v1_generation5_verified.json").write_text(json.dumps(batch,indent=2,ensure_ascii=False))
    report={"cycle":"5->6","model":MODEL,"api_calls":calls,"requested_children":len(PARENTS)*CHILDREN,
      "raw_valid_children":len(raw),"unique_candidates":len(uniq),"sample_pass":sum(r["sample"] for r in rows),
      "proved":len(verified),"research_accepted":sum(r["accepted"] for r in rows),
      "usage":dict(usage),"note":"API monetary cost must be verified in OpenAI Usage/Costs; token counts alone do not prove billed vs complimentary."}
    Path("outputs/research_agent_v1_report.json").write_text(json.dumps(report,indent=2))
    print("RESEARCH_AGENT_V1_REPORT="+json.dumps(report,sort_keys=True))
    print(f"VERIFIED_BATCH_COUNT={len(verified)}")
    if calls!=len(PARENTS): raise SystemExit("Not all parent API calls completed")
    if not verified: raise SystemExit("No verified children; refusing Melakat handoff")

if __name__=="__main__": main()
