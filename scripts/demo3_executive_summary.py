"""
=============================================================
  DEMO 3: AI-Generated Weekly IT Operations Summary
  AI in IT Business Operations — Day 2
=============================================================
Reads both datasets and generates a plain-English executive
summary — the kind a VP or Director would send to their team
or present in a Monday morning standup.

Run: python scripts/demo3_executive_summary.py
=============================================================
"""

import csv
from datetime import datetime, timedelta
from collections import Counter
import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_LICENSES  = os.path.join(BASE, "data", "software_licenses.csv")
DATA_INCIDENTS = os.path.join(BASE, "data", "it_incidents.csv")
OUTPUT_FILE    = os.path.join(BASE, "output", "demo3_executive_summary.txt")

def days_since(d): return (datetime.today() - datetime.strptime(d, "%Y-%m-%d")).days
def days_until(d): return (datetime.strptime(d, "%Y-%m-%d") - datetime.today()).days

def run():
    # ── Load license data ──
    with open(DATA_LICENSES) as f:
        licenses = list(csv.DictReader(f))

    unused       = [r for r in licenses if days_since(r["Last Used Date"]) > 90]
    overages     = [r for r in licenses if int(r["Installed Count"]) > int(r["Licensed Count"])]
    expiring     = [r for r in licenses if 0 < days_until(r["Contract Renewal"]) <= 90]
    waste_total  = sum(int(r["Annual Cost"]) for r in unused)
    critical_lic = [r for r in overages if int(r["Installed Count"]) - int(r["Licensed Count"]) >= 3
                    or int(r["Annual Cost"]) > 50000]

    # ── Load incident data ──
    with open(DATA_INCIDENTS) as f:
        incidents = list(csv.DictReader(f))

    p1_count     = sum(1 for r in incidents if r["Priority"] == "P1")
    open_tickets = [r for r in incidents if r["Status"] == "Open"]
    repeats      = [r for r in incidents if r["Repeat Issue"] == "Yes"]
    top_category = Counter(r["Category"] for r in incidents).most_common(1)[0]
    top_cause    = Counter(r["Root Cause"] for r in repeats if r["Root Cause"]).most_common(1)[0]
    breaches     = [r for r in incidents if r["Status"] == "Closed"
                    and r["Actual Hours"] and r["SLA Hours"]
                    and float(r["Actual Hours"]) > float(r["SLA Hours"])]
    breach_rate  = round(len(breaches) / len([r for r in incidents if r["Status"] == "Closed"]) * 100)

    # ── Build the summary ──
    week_label = datetime.today().strftime("%B %d, %Y")

    summary = f"""
{'='*70}
  WEEKLY IT OPERATIONS EXECUTIVE SUMMARY
  Week of {week_label}
  Prepared by: AI-Assisted IT Operations Platform
{'='*70}

OVERVIEW
--------
This week's operational data highlights three areas requiring leadership
attention: recurring infrastructure incidents, software compliance
exposure, and contract renewals due in the next 90 days.

──────────────────────────────────────────────
1. INCIDENT MANAGEMENT
──────────────────────────────────────────────
• {p1_count} P1 critical incidents were raised this period.
• {len(open_tickets)} tickets remain open and unresolved — immediate review recommended.
• {len(repeats)} incidents ({round(len(repeats)/len(incidents)*100)}%) were repeat occurrences of known issues.
• SLA breach rate: {breach_rate}% of closed tickets exceeded target resolution time.

TOP ISSUE: "{top_category[0]}" is the most frequent incident category
({top_category[1]} occurrences). The leading root cause across repeat
incidents is "{top_cause[0]}" ({top_cause[1]} cases) — this is a
systemic issue that warrants a permanent fix, not repeated patching.

RECOMMENDED ACTION: Assign a dedicated remediation task to address
"{top_cause[0]}" once and for all. Estimated incident reduction: 30–40%.

──────────────────────────────────────────────
2. SOFTWARE LICENSE & COMPLIANCE
──────────────────────────────────────────────
• {len(unused)} software titles have not been used in 90+ days.
• Potential annual savings from unused licenses: ${waste_total:,}
• {len(overages)} titles have more installs than purchased licenses (compliance risk).
• {len(critical_lic)} of these are CRITICAL — immediate remediation required.

RECOMMENDED ACTION: Review the {len(unused)} unused titles with department
heads before next quarter. Priority: ${waste_total:,} in recoverable spend.

──────────────────────────────────────────────
3. CONTRACT RENEWALS (NEXT 90 DAYS)
──────────────────────────────────────────────
• {len(expiring)} software contracts expire within 90 days.
• Combined annual value: ${sum(int(r['Annual Cost']) for r in expiring):,}

RECOMMENDED ACTION: Procurement review meeting needed this week.
Vendors: {', '.join(set(r['Vendor'] for r in expiring))}.

──────────────────────────────────────────────
SUMMARY FOR LEADERSHIP
──────────────────────────────────────────────
  Financial exposure (unused licenses)  : ${waste_total:,}
  Compliance violations                 : {len(overages)} titles
  Open incidents                        : {len(open_tickets)}
  SLA breach rate                       : {breach_rate}%
  Contracts expiring (90 days)          : {len(expiring)}

This summary was generated automatically from operational data.
No manual data preparation was required.
{'='*70}
"""
    print(summary)
    os.makedirs(os.path.join(BASE, "output"), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"  Summary saved to: {OUTPUT_FILE}\n")

if __name__ == "__main__":
    run()
