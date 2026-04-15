"""
=============================================================
  DEMO 4: Publisher Software Asset Summary
  AI in IT Business Operations — Day 2
  
  Use case raised by: Rowana (VP), 15-Apr-2026
=============================================================
Reads cisco_publishers.csv and produces a complete publisher
summary covering:
  - Consumption & utilisation % per publisher
  - Contract start and end dates
  - ACV and TCV per contract
  - Contract owner
  - Key stakeholders using the application

Run: python scripts/demo4_publisher_summary.py
=============================================================
"""

import csv
from datetime import datetime
from collections import defaultdict
import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE   = os.path.join(BASE, "data", "cisco_publishers.csv")
OUTPUT_FILE = os.path.join(BASE, "output", "demo4_publisher_summary.txt")

def fmt_usd(val):
    return f"${int(val):,}"

def days_until(date_str):
    return (datetime.strptime(date_str, "%Y-%m-%d") - datetime.today()).days

def risk_flag(cons, util, days_left):
    if days_left < 0:
        return "🔴 EXPIRED"
    if days_left <= 90:
        return "🟠 RENEW SOON"
    if util < 40:
        return "🟡 LOW USAGE"
    if cons >= 95:
        return "🔵 CRITICAL DEP"
    return "✅ HEALTHY"

def run():
    print("\n" + "="*78)
    print("  CISCO SOFTWARE PUBLISHER SUMMARY")
    print(f"  Generated: {datetime.today().strftime('%B %d, %Y')}")
    print("="*78)

    rows = []
    with open(DATA_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # ── Group by publisher ──────────────────────────────────────
    publishers = defaultdict(list)
    for r in rows:
        publishers[r["Publisher"]].append(r)

    lines = []
    total_acv = 0
    total_tcv = 0
    flagged   = []

    for pub in sorted(publishers.keys()):
        titles = publishers[pub]

        print(f"\n{'─'*78}")
        hdr = f"  PUBLISHER: {pub.upper()}  ({len(titles)} title{'s' if len(titles)>1 else ''})"
        print(hdr); lines.append(hdr)
        print(f"{'─'*78}"); lines.append("─"*78)

        col = f"  {'Title':<30} {'Cons%':>6} {'Util%':>6} {'Contract Start':<15} {'Contract End':<13} {'ACV':>13} {'TCV':>14}  Status"
        print(col); lines.append(col)
        print("  " + "-"*74); lines.append("  " + "-"*74)

        pub_acv = 0
        pub_tcv = 0

        for r in titles:
            acv      = int(r["ACV (USD)"])
            tcv      = int(r["TCV (USD)"])
            cons     = int(r["Consumption %"])
            util     = int(r["Utilisation %"])
            dl       = days_until(r["Contract End"])
            flag     = risk_flag(cons, util, dl)
            pub_acv += acv
            pub_tcv += tcv

            line = (f"  {r['Software Title']:<30} {cons:>5}% {util:>5}% "
                    f"  {r['Contract Start']:<14} {r['Contract End']:<13} "
                    f"{fmt_usd(acv):>13} {fmt_usd(tcv):>14}  {flag}")
            print(line); lines.append(line)

            # Detail row: owner + stakeholders
            detail = (f"    Owner: {r['Contract Owner']:<25} "
                      f"Stakeholders: {r['Key Stakeholders']}")
            print(detail); lines.append(detail)

            if "🔴" in flag or "🟠" in flag or "🟡" in flag:
                flagged.append((flag, r["Publisher"], r["Software Title"],
                                r["Contract End"], fmt_usd(acv)))

        pub_line = f"\n  {pub} Total  →  ACV: {fmt_usd(pub_acv)}   TCV: {fmt_usd(pub_tcv)}"
        print(pub_line); lines.append(pub_line)
        total_acv += pub_acv
        total_tcv += pub_tcv

    # ── Portfolio Summary ────────────────────────────────────────
    print(f"\n{'='*78}")
    print("  PORTFOLIO SUMMARY")
    print(f"{'='*78}")
    summary = [
        f"  Total publishers tracked   : {len(publishers)}",
        f"  Total software titles      : {len(rows)}",
        f"  Total Annual Contract Value: {fmt_usd(total_acv)}",
        f"  Total Contract Value (TCV) : {fmt_usd(total_tcv)}",
    ]
    for s in summary:
        print(s); lines.append(s)

    # ── Attention Required ───────────────────────────────────────
    if flagged:
        print(f"\n{'─'*78}")
        print("  ACTION REQUIRED")
        print(f"{'─'*78}")
        ahdr = f"  {'Flag':<14} {'Publisher':<18} {'Title':<30} {'Expiry':<13} {'ACV':>12}"
        print(ahdr); lines += [ahdr]
        print("  " + "-"*72); lines.append("  " + "-"*72)
        for flag, pub, title, exp, acv in sorted(flagged):
            aline = f"  {flag:<14} {pub:<18} {title:<30} {exp:<13} {acv:>12}"
            print(aline); lines.append(aline)

    print("\n" + "="*78)
    os.makedirs(os.path.join(BASE, "output"), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Report saved to: {OUTPUT_FILE}\n")

if __name__ == "__main__":
    run()
