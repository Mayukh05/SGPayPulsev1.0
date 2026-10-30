"""Source-grounded officeholder lookup from the JSON roster."""
import json
import re
from pathlib import Path

PATH = Path(__file__).resolve().parent / "data" / "mp_ministers_data.json"

def load_profiles():
    return json.loads(PATH.read_text(encoding="utf-8"))

def profile_answer(question):
    q = question.lower().strip()
    people = load_profiles()
    # Resolve named-person questions first.
    matched = [p for name,p in people.items() if name.lower() in q]
    if not matched:
        # Support surnames only when unambiguous and not common words.
        aliases = {"lawrence":"Lawrence Wong", "shanmugam":"K Shanmugam", "vivian":"Vivian Balakrishnan", "josephine":"Josephine Teo", "masagos":"Masagos Zulkifli", "indranee":"Indranee Thurai Rajah", "jeffrey":"Jeffrey Siow", "jasmin":"Jasmin Lau"}
        matched = [people[name] for token,name in aliases.items() if re.search(r"\b"+token+r"\b",q)]
    if matched:
        p=matched[0]
        parts=[f"### {p['name']}",f"**Current appointment (2026):** {p['current_appointment']}",f"**Constituency:** {p['constituency']}"]
        if any(x in q for x in ('previous','histor','before','career','portfolio','term','appointment','served')):
            parts.append("**Documented appointment history (not necessarily exhaustive):**")
            for h in p['historical_portfolios']:
                parts.append(f"- {h['term']}: {h['portfolio']} ([source]({h['source_url']}))")
        parts.append("**Actual individual remuneration:** Not verified in the available official records. Role-based reference salary is not the person's actual pay.")
        parts.append(f"[PMO profile]({p['profile_source_url']}) · [Current Cabinet roster]({p['current_appointment_source_url']})")
        return "\n\n".join(parts)
    # Portfolio lookup: current officeholders only, unless history is explicitly requested.
    tokens=['education','finance','defence','health','foreign affairs','home affairs','national development','transport','manpower','trade','environment','social and family','law','culture','digital development']
    matches=[t for t in tokens if t in q]
    if matches:
        historical = any(x in q for x in ('previous','history','historical','over the last','across terms','formerly','before'))
        found=[]
        for p in people.values():
            if any(t in p['current_appointment'].lower() for t in matches):
                found.append(f"- **{p['name']}**: {p['current_appointment']} ([PMO]({p['current_appointment_source_url']}))")
            elif historical:
                for h in p['historical_portfolios']:
                    if any(t in h['portfolio'].lower() for t in matches):
                        found.append(f"- **{p['name']}**, {h['term']}: {h['portfolio']} ([source]({h['source_url']}))")
        if found:
            heading='Documented officeholders (historical coverage is partial)' if historical else 'Current Cabinet appointments'
            return '### '+heading+'\n\n'+'\n'.join(found)+'\n\nHistorical records are not exhaustive.'
    if 'cabinet' in q or 'all minister' in q or 'list minister' in q:
        return '### Current Cabinet roster (21 officeholders)\n\n'+'\n'.join(f"- **{p['name']}** — {p['current_appointment']}" for p in people.values())+'\n\n[PMO roster](https://www.pmo.gov.sg/about-us/the-cabinet/)'
    return None
