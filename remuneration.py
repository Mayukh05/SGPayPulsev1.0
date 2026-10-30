"""Source-backed 2026 political remuneration facts; no individual pay estimates."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "remuneration_framework_2026.json"

def load_framework():
    return json.loads(DATA.read_text(encoding="utf-8"))

def salary_answer(question):
    q = question.lower()
    if not any(word in q for word in ("salary", "salaries", "pay", "remuneration", "allowance", "bonus", "increment", "increase", "mr4", "2026 review")):
        return None
    data = load_framework()
    sources = {s["id"]: s for s in data["sources"]}
    def cite(rate):
        s = sources[rate["source_id"]]
        return f"[Official source: {s['title']}]({s['url']})"
    def money(value):
        return "Not recorded" if value is None else f"S${value:,.0f}"
    if any(name.lower() in q for name in __import__("profile_search").load_profiles() if name != "Lawrence Wong"):
        return ("### Individual remuneration is not established\nThe published 2026 framework does not confirm this person's exact salary or individual percentage increase. "
                "Existing political appointment holders may receive a **one-off adjustment of up to 9%**, determined individually. "
                "Do not assume everyone received 9%, or that everyone is paid the MR4 reference.\n\n" + cite(data['rates'][1]))
    if "lawrence" in q or "prime minister" in q or re_search_pm(q):
        rate=data['rates'][0]
    elif "mp allowance" in q or "member of parliament" in q or "mp pay" in q or "mps" in q:
        rate=data['rates'][2]
    elif "ncmp" in q or "non-constituency" in q:
        rate=data['rates'][3]
    elif "nmp" in q or "nominated mp" in q:
        rate=data['rates'][4]
    elif "mr4" in q or "minister" in q or "increase" in q or "increment" in q:
        rate=data['rates'][1]
    else:
        return ("The revised 2026 framework includes **PM S$3.6m annual reference**, **MR4 S$1.8m annual reference**, "
                "and **MP S$18,500 monthly allowance** from 15 October 2026. These are not verified individual take-home salaries.\n\n" + cite(data['rates'][1]))
    unit=rate['unit']
    text=f"### {rate['label']} — 2026 remuneration\n\n**From 15 October 2026:** {money(rate['current'])} per {unit}."
    if rate['previous'] is not None:
        text+=f"\n\n**Earlier published reference/allowance:** {money(rate['previous'])} per {unit}."
    if rate['kind']=='framework_reference':
        text+='\n\n**Important:** This is a published *reference package*, not verified actual remuneration or take-home pay for a named person.'
    if rate['id']=='mr4':
        text+='\n\nExisting ministers are **not automatically raised to S$1.8m**. A separate one-off adjustment of **up to 9%** applies depending on individual circumstances.'
    if rate['id']=='pm':
        text+='\n\nThe PM reference is twice the MR4 benchmark. The published framework does not establish the final take-home amount.'
    return text+'\n\n'+cite(rate)

def re_search_pm(q):
    import re
    return bool(re.search(r"\bpm\b",q))
