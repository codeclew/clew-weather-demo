"""Add explicit authored labels; preserve every original field comment and source reference."""
import copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
original=ROOT/"documentation/reference/data-model-plan.json"
base=json.loads(original.read_text())
proposal=json.loads((HERE/"field-label-proposal.original.json").read_text())
assert hashlib.sha256(original.read_bytes()).hexdigest()==proposal["sourcePlanSha256"]
plan=copy.deepcopy(base)
labels={(r["model"],r["field"]):r for r in proposal["rows"]}
count=0
for model in plan["models"]:
 for field in model["fields"]:
  row=labels[(model["id"],field["id"])]
  assert row["originalPath"]==field["path"] and row["comment"]==field["meaning"]["text"]
  assert row["evidence"]==field["meaning"]["evidence"]
  field["readableName"]={"title":"Authored readable name (agent proposal)","text":row["proposedReadableName"],"evidence":copy.deepcopy(row["evidence"])}
  if (model["id"],field["id"])==("weather-card","ordering"):
   field["originalName"]={"title":"Authored exact storage field binding (agent proposal)","text":"updated_at","evidence":copy.deepcopy(row["evidence"])}
  count+=1
assert count==23 and len(plan["models"])==6
for old,new in zip(base["models"],plan["models"]):
 for a,b in zip(old["fields"],new["fields"]):
  assert a["meaning"]==b["meaning"] and a["representations"]==b["representations"] and a["path"]==b["path"]
reading_path=ROOT/"documentation/reference/reading-plan.json"
reading_base=json.loads(reading_path.read_text());reading=copy.deepcopy(reading_base)
process=next(p for p in reading["plans"] if p["subject"]=="scenario:dashboard-save-city")
field=next(m for m in base["models"] if m["id"]=="save-city-request")["fields"][0]
comment=field["meaning"]["text"].replace("|","\\|").replace("\n"," ")
block={"title":"Request fields — Markdown table","text":"This additional reference table uses the retained request-field description. The original process steps are unchanged.\n\n| Original field | Readable name | Comment |\n| --- | --- | --- |\n| `cityId` | Selected city key | "+comment+" |\n\nThis is a source-bound description, not an observed HTTP run.","evidence":copy.deepcopy(field["meaning"]["evidence"])}
section={"id":"input-table","title":"Save City request fields","navTitle":"Request fields","blocks":[block]}
assert not any(s["id"]==section["id"] for s in process["sections"])
at=next((i for i,s in enumerate(process["sections"]) if s["id"]=="confidence"),len(process["sections"]))
process["sections"].insert(at,section)
for old,new in zip(reading_base["plans"],reading["plans"]):
 restored=copy.deepcopy(new)
 if new["subject"]=="scenario:dashboard-save-city":restored["sections"]=[s for s in restored["sections"] if s["id"]!="input-table"]
 assert restored==old
for name,value in [("data-model-plan.json",plan),("reading-plan.json",reading)]:
 (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
receipt={"status":"AUTHORED_INPUTS_PREPARED_NOT_MEANING_APPROVAL","origin":"agent-proposal","originalPlanSha256":hashlib.sha256(original.read_bytes()).hexdigest(),"originalReadingPlanSha256":hashlib.sha256(reading_path.read_bytes()).hexdigest(),"fields":count,"models":len(plan["models"]),"preservation":"All original field comments, paths, representations, evidence and process reading blocks remain exact. One new unnumbered reference section is additive.","storageFieldBinding":"weather-card/ordering explicitly displays updated_at; original path 'updated_at (stored only)' and its full comment are retained.","newClaims":"Readable labels condense retained comments and keep identical evidence arrays; they remain authored proposals, not compiler-derived meanings.","publication":plan["publication"],"snapshot":plan["snapshot"]}
(HERE/"input-provenance.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"status":"READY","models":6,"fields":23,"readingReference":"question-input-table"}))
