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

# Configure stdout/stderr to use UTF-8 to prevent 'charmap' encoding errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Always run from repo root regardless of where the user calls this from
os.chdir(os.path.dirname(os.path.abspath(__file__)))

SCRIPTS = [
    ("Demo 1", "Enterprise Software License Audit",    "code_files/demo1_license_audit.py"),
    ("Demo 2", "IT Incident Analysis",                 "code_files/demo2_incident_analysis.py"),
    ("Demo 3", "AI-Generated Executive Summary",       "code_files/demo3_executive_summary.py"),
    ("Demo 4", "Publisher Software Asset Summary",     "code_files/demo4_publisher_summary.py"),
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

    run_env = os.environ.copy()
    run_env['PYTHONIOENCODING'] = 'utf-8'

    for label, title, script in SCRIPTS:
        print(f"\n  ▶  Running {label}: {title}...")
        try:
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True, text=True, encoding='utf-8', env=run_env
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
