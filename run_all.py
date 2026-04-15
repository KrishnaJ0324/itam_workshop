"""
=============================================================
  ReadyOps ITAM Demo — Run All Reports
  Criterion Networks
=============================================================
  Run this single file to generate all 4 demo reports.

  Usage:
      python run_all.py

  Reports will appear in the output/ folder.
=============================================================
"""

import subprocess
import sys
import os
from datetime import datetime

# Always run from repo root regardless of where the user calls this from
os.chdir(os.path.dirname(os.path.abspath(__file__)))

SCRIPTS = [
    ("Demo 1", "Enterprise Software License Audit",    "scripts/demo1_license_audit.py"),
    ("Demo 2", "IT Incident Analysis",                 "scripts/demo2_incident_analysis.py"),
    ("Demo 3", "AI-Generated Executive Summary",       "scripts/demo3_executive_summary.py"),
    ("Demo 4", "Publisher Software Asset Summary",     "scripts/demo4_publisher_summary.py"),
]

def banner(text, char="=", width=70):
    print("\n" + char * width)
    print(f"  {text}")
    print(char * width)

def run():
    os.makedirs("output", exist_ok=True)

    banner("ReadyOps ITAM Demo Suite", "=")
    print(f"  Criterion Networks  |  {datetime.today().strftime('%B %d, %Y')}")
    print(f"  Generating {len(SCRIPTS)} reports...")

    results = []

    for label, title, script in SCRIPTS:
        print(f"\n  ▶  Running {label}: {title}...")
        try:
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  ✔  {label} complete")
                results.append((label, title, "✔  DONE", True))
            else:
                print(f"  ✖  {label} failed")
                print(result.stderr)
                results.append((label, title, "✖  FAILED", False))
        except Exception as e:
            print(f"  ✖  {label} error: {e}")
            results.append((label, title, "✖  ERROR", False))

    # ── Summary ──────────────────────────────────────────────
    banner("All Reports Generated", "=")
    for label, title, status, ok in results:
        print(f"  {status}   {label}: {title}")

    print(f"\n  Reports saved to:  output/")
    print(f"  Files generated:")
    for f in sorted(os.listdir("output")):
        size = os.path.getsize(f"output/{f}")
        print(f"    - output/{f}  ({size:,} bytes)")

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    run()
