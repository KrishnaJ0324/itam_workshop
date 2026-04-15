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
import csv
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

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

2. it_incidents — {len(incidents)} IT incidents (Jan–Apr 2025)
   Columns: {', '.join(incidents[0].keys()) if incidents else 'N/A'}

3. cisco_publishers — {len(publishers)} software publishers
   Columns: {', '.join(publishers[0].keys()) if publishers else 'N/A'}

When answering questions:
- Be concise, executive-friendly, and use plain English
- Format numbers with $ and commas for currency
- Use clear sections and bullet points in your response
- Flag risks, anomalies, and action items clearly
- For tabular data, use markdown tables
- Always end with a 1-2 line "Key Action" recommendation

The data will be provided in the user message as JSON.
"""

# ── Build context from all data ───────────────────────────────
def build_context(query: str) -> str:
    q = query.lower()

    # Smart context selection — only send relevant data
    ctx = {}

    if any(w in q for w in ["publisher", "acv", "tcv", "contract", "owner", "stakeholder", "consumption", "utilis", "utiliz"]):
        ctx["cisco_publishers"] = publishers

    if any(w in q for w in ["license", "licence", "software", "unused", "compliance", "overage", "renewal", "expir"]):
        ctx["software_licenses"] = licenses

    if any(w in q for w in ["incident", "p1", "sla", "breach", "outage", "ticket", "open", "root cause", "repeat"]):
        ctx["it_incidents"] = incidents

    # If nothing matched, send summary of all
    if not ctx:
        ctx["software_licenses"] = licenses
        ctx["it_incidents"] = incidents
        ctx["cisco_publishers"] = publishers

    return json.dumps(ctx, indent=2)

# ── Agent call ────────────────────────────────────────────────
def ask_agent(query: str, history: list) -> str:
    if not API_KEY or API_KEY == "your_openrouter_api_key_here":
        return "⚠️  No API key found. Please add your OpenRouter key to the `.env` file and restart."

    if not query.strip():
        return ""

    context = build_context(query)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    # Include last 3 turns of history for context (6 messages)
    for msg in history[-6:]:
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
PRESETS = {
    "📋  All publishers — full view":
        "List all publishers at Cisco with their consumption %, utilisation %, ACV, TCV, contract owner, and key stakeholders.",

    "⚠️  Contracts expiring soon":
        "Which software contracts are expiring within the next 90 days(assume today's date is 2025-04-14)? Show publisher, title, expiry date, ACV, and contract owner.",

    "📉  Low utilisation titles":
        "Which software titles have utilisation below 40%? Sort by ACV descending and recommend which ones to consider dropping at renewal.",

    "💰  Portfolio spend summary":
        "Give me a total spend summary by publisher — ACV, TCV, and number of titles. Which publisher represents the highest financial exposure?",

    "🔴  P1 incident analysis":
        "Analyse all P1 critical incidents. Which departments are most affected? What are the top root causes? What immediate actions should be taken?",

    "🔁  Repeat incidents":
        "Show me all repeat incidents and their root causes. What systemic fixes would reduce the most recurrence?",

    "🏢  License compliance":
        "Which software titles have more installs than licensed? Flag the compliance risk level for each and recommend immediate actions.",

    "📊  VP briefing note":
        "Generate a weekly IT Operations executive briefing note covering license waste, compliance risks, open incidents, and top recommended actions. Write it for a VP audience.",
}

# ── Gradio UI ─────────────────────────────────────────────────
THEME = gr.themes.Base(
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
.preset-btn { 
    font-size: 13px !important; 
    padding: 8px 14px !important; 
    border-radius: 8px !important;
    border: 1px solid #E2E8F0 !important;
    background: #F8FAFC !important;
    color: #1B2A4A !important;
    text-align: left !important;
    transition: all 0.15s !important;
}
.preset-btn:hover { 
    background: #EFF6FF !important; 
    border-color: #2E74B5 !important;
}
#header { 
    background: linear-gradient(135deg, #1B2A4A 0%, #2E74B5 100%);
    padding: 24px 28px;
    border-radius: 12px;
    margin-bottom: 16px;
}
#chatbox { min-height: 420px; }
.criterion-tag {
    font-size: 11px;
    color: #94A3B8;
    text-align: center;
    margin-top: 8px;
}
"""

def set_prompt(prompt_text):
    return prompt_text

with gr.Blocks(title="ReadyOps ITAM Agent") as demo:

    # ── Header ──────────────────────────────────────────────────
    gr.HTML("""
    <div id="header">
        <div style="display:flex; align-items:center; gap:16px;">
            <div>
                <div style="font-size:22px; font-weight:700; color:#FFFFFF; letter-spacing:-0.3px;">
                    ReadyOps ITAM Agent
                </div>
                <div style="font-size:13px; color:#93C5FD; margin-top:4px;">
                    AI-powered IT Asset Management  ·  Criterion Networks  ·  Cisco Live 2026
                </div>
            </div>
            <div style="margin-left:auto; background:rgba(255,255,255,0.12); 
                        padding:6px 14px; border-radius:20px; 
                        font-size:12px; color:#E0F2FE; font-weight:500;">
                Claude via OpenRouter
            </div>
        </div>
    </div>
    """)

    with gr.Row(equal_height=False):

        # ── Left: preset buttons ────────────────────────────────
        with gr.Column(scale=1, min_width=260):
            gr.Markdown("### Quick reports")
            gr.Markdown(
                "<span style='font-size:12px;color:#64748B;'>"
                "Click any button to load the prompt, then hit **Ask**."
                "</span>"
            )
            gr.Markdown("---")

            preset_buttons = []
            for label, prompt in PRESETS.items():
                btn = gr.Button(label, elem_classes=["preset-btn"], size="sm")
                preset_buttons.append((btn, prompt))

            gr.Markdown("---")
            gr.Markdown(
                "<div class='criterion-tag'>"
                "Data: 35 publishers · 25 licenses · 50 incidents"
                "</div>"
            )

        # ── Right: chat ─────────────────────────────────────────
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                elem_id="chatbox",
                label="",
                show_label=False,
                render_markdown=True,
                height=460,
                avatar_images=(None, "https://img.icons8.com/fluency/48/robot-2.png"),
            )

            with gr.Row():
                txt = gr.Textbox(
                    placeholder='Ask anything — e.g. "Who owns the Workday contract?"',
                    show_label=False,
                    scale=5,
                    lines=1,
                    container=False,
                )
                ask_btn = gr.Button("Ask →", variant="primary", scale=1, min_width=80)
                clear_btn = gr.Button("Clear", variant="secondary", scale=1, min_width=70)

            gr.Markdown(
                "<span style='font-size:11px;color:#94A3B8;'>"
                "Tip: Click a quick report button or type your own question above."
                "</span>"
            )

    # ── State ───────────────────────────────────────────────────
    history = gr.State([])

    # ── Event handlers ──────────────────────────────────────────
    def respond(message, hist):
        if not message.strip():
            return hist, hist, ""
        reply = ask_agent(message, hist)
        hist = hist + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
        return hist, hist, ""

    def clear_chat():
        return [], [], ""

    ask_btn.click(respond,  inputs=[txt, history], outputs=[chatbot, history, txt])
    txt.submit(respond,     inputs=[txt, history], outputs=[chatbot, history, txt])
    clear_btn.click(clear_chat,                    outputs=[chatbot, history, txt])

    # Wire preset buttons
    for btn, prompt_text in preset_buttons:
        btn.click(lambda p=prompt_text: p, outputs=[txt])

# ── Launch ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ReadyOps ITAM Agent")
    print("  Criterion Networks  ·  Cisco Live 2026")
    print("="*60)
    if not API_KEY or API_KEY == "your_openrouter_api_key_here":
        print("\n  ⚠️  No API key detected.")
        print("  Copy .env.example to .env and add your OpenRouter key.")
    else:
        print("\n  ✔  API key loaded")
    print(f"\n  Data loaded:")
    print(f"    · {len(publishers)} publishers  (cisco_publishers.csv)")
    print(f"    · {len(licenses)} software titles  (software_licenses.csv)")
    print(f"    · {len(incidents)} incidents  (it_incidents.csv)")
    print("\n  Starting server → http://localhost:7860\n")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True, theme=THEME, css=CSS)
