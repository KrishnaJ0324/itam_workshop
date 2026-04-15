"""
=============================================================
  DEMO 1: Software License Audit
  AI in IT Business Operations — Day 2
=============================================================
Reads software_licenses.csv and surfaces:
  - Licenses unused for 90+ days (cost recovery opportunities)
  - Compliance violations (installed > licensed)
  - Contracts expiring within 90 days
  - Total financial exposure

Run: python scripts/demo1_license_audit.py
=============================================================
"""

import csv
from datetime import datetime, timedelta
import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UNUSED_DAYS     = 90
HIGH_PRIORITY   = 10000
EXPIRY_WARN     = 90   # days
DATA_FILE       = os.path.join(BASE, "data", "software_licenses.csv")
OUTPUT_FILE     = os.path.join(BASE, "output", "demo1_license_audit.txt")

def days_since(date_str):
    return (datetime.today() - datetime.strptime(date_str, "%Y-%m-%d")).days

def days_until(date_str):
    return (datetime.strptime(date_str, "%Y-%m-%d") - datetime.today()).days

def run():
    print("\n" + "="*70)
    print("  ENTERPRISE SOFTWARE LICENSE AUDIT")
    print(f"  Generated: {datetime.today().strftime('%B %d, %Y')}")
    print("="*70)

    unused, overages, expiring = [], [], []

    with open(DATA_FILE) as f:
        for row in csv.DictReader(f):
            cost        = int(row["Annual Cost"])
            licensed    = int(row["Licensed Count"])
            installed   = int(row["Installed Count"])
            last_used   = row["Last Used Date"]
            renewal     = row["Contract Renewal"]

            # Unused licenses
            d = days_since(last_used)
            if d > UNUSED_DAYS:
                unused.append({
                    "name": row["Software Name"], "dept": row["Department"],
                    "owner": row["Owner"], "days": d, "cost": cost,
                    "flag": "⚠ HIGH PRIORITY" if cost >= HIGH_PRIORITY else ""
                })

            # Compliance overage
            if installed > licensed:
                overage = installed - licensed
                risk = "🔴 CRITICAL" if overage >= 3 or cost > 50000 else "🟠 HIGH" if overage == 2 else "🟡 MEDIUM"
                overages.append({
                    "name": row["Software Name"], "vendor": row["Vendor"],
                    "dept": row["Department"], "licensed": licensed,
                    "installed": installed, "overage": overage,
                    "cost": cost, "risk": risk
                })

            # Expiring contracts
            days_left = days_until(renewal)
            if 0 < days_left <= EXPIRY_WARN:
                expiring.append({
                    "name": row["Software Name"], "owner": row["Owner"],
                    "renewal": renewal, "days_left": days_left, "cost": cost
                })

    lines = []

    # ── Section 1: Unused Licenses ──
    print(f"\n{'─'*70}")
    print("  SECTION 1 — UNUSED LICENSES (not used in 90+ days)")
    print(f"{'─'*70}")
    unused.sort(key=lambda x: x["cost"], reverse=True)
    hdr = f"  {'Software':<28} {'Department':<18} {'Days Unused':>11} {'Annual Cost':>12}  Flag"
    print(hdr); print("  " + "-"*64)
    lines += [hdr, "  " + "-"*64]
    total_waste = 0
    for u in unused:
        line = f"  {u['name']:<28} {u['dept']:<18} {u['days']:>11} ${u['cost']:>11,}  {u['flag']}"
        print(line); lines.append(line)
        total_waste += u["cost"]
    summary = f"\n  Total unused licenses: {len(unused)}  |  Potential annual savings: ${total_waste:,}"
    print(summary); lines.append(summary)

    # ── Section 2: Compliance Overages ──
    print(f"\n{'─'*70}")
    print("  SECTION 2 — COMPLIANCE OVERAGES (installed > licensed)")
    print(f"{'─'*70}")
    overages.sort(key=lambda x: x["overage"], reverse=True)
    hdr2 = f"  {'Software':<28} {'Vendor':<14} {'Licensed':>9} {'Installed':>10} {'Over':>5}  Risk"
    print(hdr2); print("  " + "-"*64)
    lines += [hdr2, "  " + "-"*64]
    for o in overages:
        line = f"  {o['name']:<28} {o['vendor']:<14} {o['licensed']:>9} {o['installed']:>10} {o['overage']:>5}  {o['risk']}"
        print(line); lines.append(line)

    # ── Section 3: Expiring Contracts ──
    print(f"\n{'─'*70}")
    print(f"  SECTION 3 — CONTRACTS EXPIRING WITHIN {EXPIRY_WARN} DAYS")
    print(f"{'─'*70}")
    expiring.sort(key=lambda x: x["days_left"])
    hdr3 = f"  {'Software':<28} {'Owner':<22} {'Renewal Date':<14} {'Days Left':>9} {'Annual Cost':>12}"
    print(hdr3); print("  " + "-"*64)
    lines += [hdr3, "  " + "-"*64]
    for e in expiring:
        line = f"  {e['name']:<28} {e['owner']:<22} {e['renewal']:<14} {e['days_left']:>9} ${e['cost']:>11,}"
        print(line); lines.append(line)

    print("\n" + "="*70)
    os.makedirs(os.path.join(BASE, "output"), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Report saved to: {OUTPUT_FILE}\n")

if __name__ == "__main__":
    run()
