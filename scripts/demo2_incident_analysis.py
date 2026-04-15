"""
=============================================================
  DEMO 2: IT Incident Data Analysis
  AI in IT Business Operations — Day 2
=============================================================
Reads it_incidents.csv and surfaces:
  - Top recurring issues and root causes
  - SLA breach analysis by team and priority
  - Departments generating the most P1 incidents
  - Open tickets requiring attention

Run: python scripts/demo2_incident_analysis.py
=============================================================
"""

import csv
from datetime import datetime
from collections import Counter, defaultdict
import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE   = os.path.join(BASE, "data", "it_incidents.csv")
OUTPUT_FILE = os.path.join(BASE, "output", "demo2_incident_analysis.txt")

def run():
    print("\n" + "="*70)
    print("  IT INCIDENT ANALYSIS REPORT")
    print(f"  Generated: {datetime.today().strftime('%B %d, %Y')}")
    print(f"  Period: January – April 2025")
    print("="*70)

    rows = []
    with open(DATA_FILE) as f:
        rows = list(csv.DictReader(f))

    closed = [r for r in rows if r["Status"] == "Closed"]
    open_  = [r for r in rows if r["Status"] == "Open"]
    p1     = [r for r in rows if r["Priority"] == "P1"]

    # SLA breaches
    breaches = []
    for r in closed:
        if r["Actual Hours"] and r["SLA Hours"]:
            if float(r["Actual Hours"]) > float(r["SLA Hours"]):
                breaches.append(r)

    lines = []

    # ── Section 1: Volume Summary ──
    cats    = Counter(r["Category"] for r in rows)
    depts   = Counter(r["Department"] for r in p1)
    repeats = [r for r in rows if r["Repeat Issue"] == "Yes"]

    print(f"\n{'─'*70}")
    print("  SECTION 1 — INCIDENT VOLUME SUMMARY")
    print(f"{'─'*70}")
    summary = [
        f"  Total incidents          : {len(rows)}",
        f"  P1 Critical incidents    : {len(p1)}",
        f"  Repeat / recurring issues: {len(repeats)} ({round(len(repeats)/len(rows)*100)}%)",
        f"  SLA breaches             : {len(breaches)} ({round(len(breaches)/len(closed)*100)}% of closed)",
        f"  Currently open           : {len(open_)}",
    ]
    for s in summary:
        print(s); lines.append(s)

    # ── Section 2: Top Categories ──
    print(f"\n{'─'*70}")
    print("  SECTION 2 — TOP INCIDENT CATEGORIES")
    print(f"{'─'*70}")
    hdr = f"  {'Category':<28} {'Count':>6}  {'% of Total':>10}"
    print(hdr); print("  " + "-"*48); lines += [hdr, "  " + "-"*48]
    for cat, count in cats.most_common(8):
        pct = round(count / len(rows) * 100)
        bar = "█" * (pct // 5)
        line = f"  {cat:<28} {count:>6}  {bar:<12} {pct}%"
        print(line); lines.append(line)

    # ── Section 3: Recurring Root Causes ──
    print(f"\n{'─'*70}")
    print("  SECTION 3 — RECURRING ROOT CAUSES")
    print(f"{'─'*70}")
    causes = Counter(r["Root Cause"] for r in repeats)
    hdr3 = f"  {'Root Cause':<38} {'Occurrences':>12}"
    print(hdr3); print("  " + "-"*52); lines += [hdr3, "  " + "-"*52]
    for cause, count in causes.most_common():
        line = f"  {cause:<38} {count:>12}"
        print(line); lines.append(line)

    # ── Section 4: SLA Breaches by Team ──
    print(f"\n{'─'*70}")
    print("  SECTION 4 — SLA BREACHES BY ASSIGNED TEAM")
    print(f"{'─'*70}")
    team_breach = Counter(r["Assigned Team"] for r in breaches)
    team_total  = Counter(r["Assigned Team"] for r in closed)
    hdr4 = f"  {'Team':<20} {'Breaches':>9} {'Total':>7}  {'Breach Rate':>12}"
    print(hdr4); print("  " + "-"*52); lines += [hdr4, "  " + "-"*52]
    for team, b_count in team_breach.most_common():
        total = team_total.get(team, 0)
        rate  = round(b_count / total * 100) if total else 0
        flag  = "  ⚠" if rate > 50 else ""
        line  = f"  {team:<20} {b_count:>9} {total:>7}  {rate:>10}%{flag}"
        print(line); lines.append(line)

    # ── Section 5: P1 Incidents by Department ──
    print(f"\n{'─'*70}")
    print("  SECTION 5 — P1 INCIDENTS BY DEPARTMENT")
    print(f"{'─'*70}")
    hdr5 = f"  {'Department':<22} {'P1 Count':>9}"
    print(hdr5); print("  " + "-"*33); lines += [hdr5, "  " + "-"*33]
    for dept, count in depts.most_common():
        line = f"  {dept:<22} {count:>9}"
        print(line); lines.append(line)

    # ── Section 6: Open Tickets ──
    print(f"\n{'─'*70}")
    print("  SECTION 6 — OPEN TICKETS REQUIRING ATTENTION")
    print(f"{'─'*70}")
    hdr6 = f"  {'Ticket':<12} {'Category':<24} {'Priority':<10} {'Department':<20} {'Created'}"
    print(hdr6); print("  " + "-"*68); lines += [hdr6, "  " + "-"*68]
    for r in open_:
        line = f"  {r['Ticket ID']:<12} {r['Category']:<24} {r['Priority']:<10} {r['Department']:<20} {r['Created Date']}"
        print(line); lines.append(line)

    print("\n" + "="*70)
    os.makedirs(os.path.join(BASE, "output"), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Report saved to: {OUTPUT_FILE}\n")

if __name__ == "__main__":
    run()
