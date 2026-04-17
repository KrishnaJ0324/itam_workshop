"""
=============================================================
  ReadyOps ITAM Agent
  Criterion Networks  ·  Cisco Live 2026
=============================================================
  AI-powered IT Asset Management reporting agent.
  Backed by Claude via OpenRouter.

  Setup:
    1. Copy .env.example to .env
    2. Add your OpenRouter API key
    3. Run:  python agent.py
    4. Open browser at http://localhost:7860
=============================================================
"""

import os
import re
import csv
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
from fpdf import FPDF

# ── Load environment ──────────────────────────────────────────
load_dotenv()
BASE    = Path(__file__).parent
API_KEY = os.getenv("OPENROUTER_API_KEY", "")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

# ── Load all CSV data at startup ──────────────────────────────
def load_csv(filename):
    path = BASE / "data" / filename
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

licenses   = load_csv("software_licenses.csv")
incidents  = load_csv("it_incidents.csv")
publishers = load_csv("cisco_publishers.csv")

def data_summary():
    return {
        "software_licenses":  {"rows": len(licenses),   "columns": list(licenses[0].keys())   if licenses   else []},
        "it_incidents":       {"rows": len(incidents),  "columns": list(incidents[0].keys())  if incidents  else []},
        "cisco_publishers":   {"rows": len(publishers), "columns": list(publishers[0].keys()) if publishers else []},
    }

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are the ReadyOps ITAM Agent for Criterion Networks.
You are a knowledgeable IT Asset Management and Software Asset Management assistant.
You have access to three datasets:

1. software_licenses — {len(licenses)} enterprise software titles
   Columns: {', '.join(licenses[0].keys()) if licenses else 'N/A'}

2. it_incidents — {len(incidents)} IT incidents
   Columns: {', '.join(incidents[0].keys()) if incidents else 'N/A'}

3. cisco_publishers — {len(publishers)} software publishers
   Columns: {', '.join(publishers[0].keys()) if publishers else 'N/A'}

When answering questions, structure your response as a professional executive brief:
1. **Executive Summary**: Start with a brief 1-2 paragraph narrative summarizing the core findings.
2. **Key Insights**: Use bullet points to highlight critical metrics, risks, and anomalies.
3. **Data Overview**: Sparingly use markdown tables ONLY if displaying more than 3 rows of comparative numerical data. Otherwise, weave the data naturally into your narrative. DO NOT just dump raw tables.
4. **Key Action**: End with a clear recommendation section.

Formatting guidelines:
- Be concise, executive-friendly, and use plain English.
- Format numbers with $ and commas for currency.
- Do not hallucinate or assume data that is not explicitly present.

The data will be provided in the user message as JSON.
"""

# ── Build context from all data ───────────────────────────────
def build_context(query: str) -> str:
    q = query.lower()

    # Smart context selection — only send relevant data
    ctx = {}

    if any(w in q for w in ["publisher", "acv", "tcv", "contract", "owner", "stakeholder", "consumption", "utilise", "utilize"]):
        ctx["cisco_publishers"] = publishers

    if any(w in q for w in ["license", "licence", "software", "unused", "compliance", "overage", "renewal", "expiry"]):
        ctx["software_licenses"] = licenses

    if any(w in q for w in ["incident", "p1", "sla", "breach", "outage", "ticket", "open", "root cause", "repeat"]):
        ctx["it_incidents"] = incidents

    # If nothing matched, send summary of all
    if not ctx:
        ctx["software_licenses"] = licenses
        ctx["it_incidents"] = incidents
        ctx["cisco_publishers"] = publishers

    return json.dumps(ctx, indent=2)

# ── Detect if query is asking for a report ────────────────────
REPORT_KEYWORDS = [
    "report", "download", "export", "generate", "briefing", "summary",
    "analysis","breakdown", "overview", "audit",
]

def is_report_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in REPORT_KEYWORDS)

# ── PDF Generation ────────────────────────────────────────────
class ITAMReportPDF(FPDF):
    """Branded ReadyOps ITAM PDF report."""

    BRAND_DARK  = (27,  42,  74)   # #1B2A4A
    BRAND_BLUE  = (46, 116, 181)   # #2E74B5
    BRAND_LIGHT = (248, 250, 252)  # #F8FAFC
    TEXT_MAIN   = (15,  23,  42)   # near-black
    TEXT_MUTED  = (100, 116, 139)  # slate-500

    def __init__(self, report_title: str):
        super().__init__()
        self.report_title = report_title
        self.set_auto_page_break(auto=True, margin=20)
        self.add_page()

    def header(self):
        from fpdf.enums import XPos, YPos
        self.set_fill_color(*self.BRAND_DARK)
        self.rect(0, 0, 210, 28, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 8)
        self.cell(120, 6, "ReadyOps ITAM Agent", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(147, 197, 253)
        self.set_xy(10, 16)
        self.cell(120, 5, "Criterion Networks  -  Cisco Live 2026", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(224, 242, 254)
        ts = datetime.now().strftime("%Y-%m-%d  %H:%M")
        self.set_xy(140, 11)
        self.cell(60, 6, ts, align="R", new_x=XPos.RIGHT, new_y=YPos.TOP)
        
        # Explicitly move the cursor below the 28-unit banner so text doesn't overlap
        self.set_y(35)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*self.TEXT_MUTED)
        self.cell(0, 8, f"ReadyOps ITAM  -  Criterion Networks  -  Page {self.page_no()}", align="C")

    def add_report_title(self, title: str):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*self.BRAND_DARK)
        self.ln(4)
        self.multi_cell(0, 9, title)
        self.set_draw_color(*self.BRAND_BLUE)
        self.set_line_width(0.6)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(7)

    def add_section_heading(self, text: str):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.BRAND_BLUE)
        self.ln(4)
        self.multi_cell(0, 7, text)
        self.ln(1)
        self.set_text_color(*self.TEXT_MAIN)

    def add_body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.TEXT_MAIN)
        self.multi_cell(0, 6, text)
        self.ln(1)

    def add_bullet(self, text: str, level: int = 0):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.TEXT_MAIN)
        indent = 10 + level * 8
        bullet = "-" if level == 0 else "  o"
        self.set_x(10 + indent)
        self.multi_cell(0, 6, f"{bullet}  {text}")

    def add_table(self, headers: list[str], rows: list[list[str]]):
        self.ln(2)
        
        # Safely determine the max columns to prevent X-overflow crashing
        max_cols = len(headers)
        for row in rows:
            max_cols = max(max_cols, len(row))
            
        if max_cols == 0:
            return
            
        # Hard cap the columns so they never squeeze text to 0 width
        max_cols = min(max_cols, 8)
        
        page_w   = 190
        col_w    = page_w / max_cols

        self.set_fill_color(*self.BRAND_DARK)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 9)
        
        # Normalize headers to match exact column count
        safe_headers = headers[:max_cols]
        safe_headers += [""] * (max_cols - len(safe_headers))
        
        for h in safe_headers:
            self.cell(col_w, 7, str(h)[:28], border=0, fill=True, align="C")
        self.ln()

        self.set_font("Helvetica", "", 8.5)
        for i, row in enumerate(rows):
            fill = i % 2 == 0
            self.set_fill_color(240, 245, 255) if fill else self.set_fill_color(255, 255, 255)
            self.set_text_color(*self.TEXT_MAIN)
            
            # Normalize row cells to match exact column count
            safe_row = row[:max_cols]
            safe_row += [""] * (max_cols - len(safe_row))
            
            for cell in safe_row:
                self.cell(col_w, 6.5, str(cell)[:28], border=0, fill=True)
            self.ln()

        self.set_draw_color(*self.BRAND_BLUE)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)


def sanitize_text(text: str) -> str:
    replacements = {
        "\u2022": "-", "\u25e6": "o", "\u2013": "-", "\u2014": "--", 
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', 
        "\u2026": "...", "\u2192": "->", "\u2190": "<-", "\u00b7": ".", 
        "\u00b0": " deg", "\u00d7": "x", "\u00f7": "/", "\u2264": "<=", 
        "\u2265": ">=", "\u00a9": "(c)", "\u00ae": "(R)", "\u2122": "(TM)", 
        "\u20ac": "EUR", "\u00a3": "GBP",
    }
    for uni, asc in replacements.items():
        text = text.replace(uni, asc)
        
    # Break up abnormally long strings (e.g., ----------------) that crash FPDF word wrap
    text = re.sub(r'([^\s]{80})', r'\1 ', text)

    # FIX: Globally remove ** markdown bold markers to prevent spacing issues
    text = text.replace("**", "")
    
    return text.encode("latin-1", errors="replace").decode("latin-1")


def parse_markdown_to_pdf(pdf: ITAMReportPDF, md_text: str):
    md_text = sanitize_text(md_text)
    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
            rows = []
            for tl in table_lines[2:]:
                cells = [c.strip() for c in tl.strip("|").split("|")]
                if any(c for c in cells):
                    rows.append(cells)
            if headers:
                pdf.add_table(headers, rows)
            continue

        if line.startswith("### "):
            pdf.add_section_heading(line[4:].strip())
        elif line.startswith("## "):
            pdf.add_section_heading(line[3:].strip())
        elif line.startswith("# "):
            pdf.add_section_heading(line[2:].strip())
        elif line.startswith("- ") or line.startswith("* "):
            pdf.add_bullet(line[2:].strip())
        elif re.match(r"^\s+[-*] ", line):
            pdf.add_bullet(line.strip()[2:].strip(), level=1)
        elif line.strip() in ("---", "***", "___"):
            pdf.set_draw_color(*ITAMReportPDF.BRAND_BLUE)
            pdf.set_line_width(0.3)
            pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
            pdf.ln(5)
        elif line.strip():
            clean = re.sub(r"\*(.*?)\*",     r"\1", line) 
            clean = re.sub(r"`(.*?)`",       r"\1", clean) 
            pdf.add_body_text(clean.strip())
        else:
            pdf.ln(2)

        i += 1


def generate_pdf(query: str, report_text: str) -> str:
    pdf = ITAMReportPDF(report_title="ITAM Report")
    pdf.ln(4)
    parse_markdown_to_pdf(pdf, report_text)

    # Use context manager to acquire the path, and immediately release the Windows file lock
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="ITAM_Report_") as temp_file:
        temp_path = temp_file.name
    
    # FPDF can now safely write
    pdf.output(temp_path)
    return temp_path


# ── Agent call ────────────────────────────────────────────────
def ask_agent(query: str, history: list) -> str:
    if not API_KEY or API_KEY == "your_openrouter_api_key_here":
        return "⚠️  No API key found. Please add your OpenRouter key to the `.env` file and restart."
    if not query.strip(): return ""

    context = build_context(query)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in history[-6:]:
        if isinstance(msg.get("content"), str):
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({
        "role": "user",
        "content": f"{query}\n\n---\nDATA:\n{context}"
    })

    try:
        response = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            max_tokens=2000,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️  Error calling Claude: {str(e)}"

# ── Preset prompts ────────────────────────────────────────────
def load_prompts(filename):
    path = BASE / "doc" / filename
    if not path.exists(): return []
    with open(path, encoding="utf-8") as f:
        prompts = []
        for line in f:
            line = line.strip()
            if line and not line.startswith("🔹"):
                c = line.strip('“”"')
                if c: prompts.append(c)
        return prompts

PROMPT_GROUPS = {
    "Software Licenses": load_prompts("prompts_1.txt"),
    "IT Incidents": load_prompts("prompts_2.txt"),
    "Publishers": load_prompts("prompts_3.txt")
}

# ── Gradio UI ─────────────────────────────────────────────────
THEME = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
).set(
    body_background_fill="#F8FAFC",
    block_background_fill="#FFFFFF",
    block_border_color="#E2E8F0",
    block_shadow="0 1px 3px rgba(0,0,0,0.08)",
    button_primary_background_fill="#1B2A4A",
    button_primary_background_fill_hover="#2E74B5",
    button_primary_text_color="#FFFFFF",
)

CSS = """
.preset-btn { font-size: 13px !important; padding: 8px 14px !important; border-radius: 8px !important; border: 1px solid var(--border-color-primary) !important; background: var(--background-fill-secondary) !important; color: var(--body-text-color) !important; text-align: left !important; transition: all 0.15s !important; }
.preset-btn:hover { background: var(--background-fill-primary) !important; border-color: var(--color-accent) !important; }
#header { background: linear-gradient(135deg, #1B2A4A 0%, #2E74B5 100%); padding: 24px 28px; border-radius: 12px; margin-bottom: 16px; }

/* Force the chatbox to stand out with a solid background and shadow */
#chatbox { 
    min-height: 420px; 
    background: var(--block-background-fill) !important;
    border: 1px solid var(--block-border-color) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
}

#chatbox strong { color: var(--color-accent); font-weight: 700; }
.criterion-tag { font-size: 11px; color: var(--body-text-color-subdued); text-align: center; margin-top: 8px; }
#pdf-download-row { padding: 10px 0px; margin-top: 6px; }
"""

with gr.Blocks(title="ReadyOps ITAM Agent") as demo:

    gr.HTML("""
    <div id="header">
        <div style="display:flex; align-items:center; gap:16px;">
            <div>
                <div style="font-size:22px; font-weight:700; color:#FFFFFF; letter-spacing:-0.3px;">ReadyOps ITAM Agent</div>
                <div style="font-size:13px; color:#93C5FD; margin-top:4px;">AI-powered IT Asset Management  ·  Criterion Networks  ·  Cisco Live 2026</div>
            </div>
            <div style="margin-left:auto; background:rgba(255,255,255,0.12); padding:6px 14px; border-radius:20px; font-size:12px; color:#E0F2FE; font-weight:500;">Claude via OpenRouter</div>
        </div>
    </div>
    """)

    with gr.Row(equal_height=False):
        with gr.Column(scale=1, min_width=260):
            gr.Markdown("### Quick Prompts\n<span style='font-size:12px;color:#64748B;'>Select a dataset below to view and select prompts.</span>\n---")
            preset_buttons = []
            
            for group_name, prompts_list in PROMPT_GROUPS.items():
                with gr.Accordion(group_name, open=False):
                    for prompt in prompts_list:
                        btn = gr.Button(prompt, elem_classes=["preset-btn"], size="sm")
                        preset_buttons.append((btn, prompt))
            
            gr.Markdown("---\n<div class='criterion-tag'>Data: 35 publishers · 25 licenses · 50 incidents</div>")

        with gr.Column(scale=3):
            chatbot = gr.Chatbot(elem_id="chatbox", show_label=False, render_markdown=True, height=460, avatar_images=(None, "https://img.icons8.com/fluency/48/robot-2.png"))

            with gr.Row():
                txt = gr.Textbox(placeholder='Ask anything — e.g. "Who owns the Workday contract?"', show_label=False, scale=5, lines=1, container=False)
                ask_btn   = gr.Button("Ask →",  variant="primary",   scale=1, min_width=80)
                clear_btn = gr.Button("Clear",   variant="secondary", scale=1, min_width=70)

            # SWAPPED TO DOWNLOAD BUTTON: Bypasses the browser's buggy PDF preview renderer
            with gr.Row(elem_id="pdf-download-row", visible=False) as pdf_row:
                download_btn = gr.DownloadButton("📄 Click here to Download PDF Report", variant="primary", visible=True, size="lg")

            gr.Markdown("<span style='font-size:11px;color:#94A3B8;'>Tip: Select a quick prompt or type your own question above. Reports can also be auto-generated as downloadable PDFs.</span>")

    history = gr.State([])

    def respond(message, hist):
        if not message.strip():
            return hist, hist, "", gr.update(visible=False), gr.update(value=None)

        reply = ask_agent(message, hist)
        hist  = hist + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]

        if is_report_query(message):
            try:
                pdf_path = generate_pdf(message, reply)
                # Ensure the button receives the path and becomes visible
                return hist, hist, "", gr.update(visible=True), gr.update(value=pdf_path)
            except Exception as e:
                print(f"[PDF generation error] {e}")
                return hist, hist, "", gr.update(visible=False), gr.update(value=None)

        return hist, hist, "", gr.update(visible=False), gr.update(value=None)

    def clear_chat():
        return [], [], "", gr.update(visible=False), gr.update(value=None)

    respond_outputs = [chatbot, history, txt, pdf_row, download_btn]

    ask_btn.click(respond, inputs=[txt, history], outputs=respond_outputs)
    txt.submit(respond,    inputs=[txt, history], outputs=respond_outputs)
    clear_btn.click(clear_chat, outputs=respond_outputs)

    for btn, prompt_text in preset_buttons:
        btn.click(lambda p=prompt_text: p, outputs=[txt])

# ── Launch ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ReadyOps ITAM Agent")
    print("  Criterion Networks  ·  Cisco Live 2026")
    print("="*60)
    
    # CRITICAL: Allow Gradio to serve files from the system's temporary directory
    temp_dir = tempfile.gettempdir()
    
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        theme=THEME,
        css=CSS,
        allowed_paths=[temp_dir]
    )