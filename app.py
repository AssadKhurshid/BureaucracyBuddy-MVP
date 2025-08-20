# app.py — Spyder-friendly + multi-provider + Word/PDF download + PRO gradient UI
import os, sys, subprocess, requests
from typing import List, Dict

# -------- Spyder-friendly relaunch under Streamlit --------
def _running_under_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore
        return get_script_run_ctx() is not None
    except Exception:
        return False

if not _running_under_streamlit():
    script_path = os.path.abspath(__file__)
    cmd = [sys.executable, "-m", "streamlit", "run", script_path]
    subprocess.run(cmd)
    sys.exit(0)

# -------------------- App code --------------------
import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

st.set_page_config(page_title="Bureaucracy Buddy (MVP)", page_icon="📬", layout="wide")

# -------- Custom CSS (gradient, polished inputs/buttons, hero) --------
st.markdown(
    """
    <style>
    /* App background gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #0ea5e9 130%);
        background-attachment: fixed;
        color: #f8fafc;
    }
    /* Sidebar gradient + spacing */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
        color: #f9fafb;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    /* Hero card */
    .hero {
        background: linear-gradient(135deg, rgba(15,23,42,0.6), rgba(14,165,233,0.15));
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        border-radius: 18px;
        padding: 24px 28px;
        margin-bottom: 18px;
        margin-top: 40px;
        margin-right: 40px;
        backdrop-filter: blur(6px);
    }
    .hero h1 {
        margin: 0 0 8px 0; color: #f8fafc; font-size: 2.0rem;
    }
    .hero p, .hero li { color: #e5e7eb; }

    /* Cards / containers */
    .card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 16px 16px 8px 16px;
        margin-bottom: 14px;
        backdrop-filter: blur(4px);
    }

    /* Headings */
    h2, h3, .stMarkdown h2, .stMarkdown h3 { color: #f3f4f6 !important; }

    /* Inputs */
    textarea, input, .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background: #0b1220 !important;
        color: #f9fafb !important;
        border-radius: 12px !important;
        border: 1px solid rgba(148,163,184,0.35) !important;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #38bdf8 0%, #22d3ee 100%) !important;
        color: #0b1220 !important;
        border: 0 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 0.65rem 1.2rem !important;
        box-shadow: 0 8px 22px rgba(34,211,238,0.25);
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #34d399 0%, #22d3ee 100%) !important;
        box-shadow: 0 10px 28px rgba(34,211,238,0.35);
    }

    /* Download buttons (use same style) */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #818cf8 0%, #22d3ee 100%) !important;
        color: #0b1220 !important;
        border: 0 !important; border-radius: 12px !important;
        font-weight: 700 !important; padding: 0.55rem 1.0rem !important;
    }

    /* Divider line subtle */
    hr { border: none; height: 1px; background: rgba(255,255,255,0.1); }

    /* Reduce excessive top/bottom whitespace */
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------- Optional logo (safe if file is missing) --------
logo_path = "E:/BureaucracyBuddy-MVP/logo.png"
col_logo, col_title = st.columns([1, 6])
with col_logo:
    try:
        st.image(logo_path, width=64)
    except Exception:
        st.empty()

# -------- HERO HEADER --------
with col_title:
    st.markdown(
        """
        <div class="hero">
          <h1>📬 Bureaucracy Buddy — German Letters Made Easy (MVP)</h1>
          <ul>
            <li><b>Summarize</b> (plain-language TL;DR)</li>
            <li><b>Extract key details</b> (dates, deadlines, requirements, sender, reference IDs)</li>
            <li><b>Draft a reply</b> (polite German email/letter; choose tone)</li>
            <li><b>Translate</b> (EN ↔ DE; Plain German option)</li>
            <li><b>Create checklist</b> (action items you must do)</li>
          </ul>
          <p>No sign-up. Results are <b>fully editable</b> below.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------- Sidebar (Provider & Keys) ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    provider = st.selectbox(
        "Provider",
        ["Groq (Llama-3)", "Together (Mixtral/Llama)", "Hugging Face Inference API", "Ollama (local)", "OpenAI"],
        index=0,
    )
    default_models = {
        "OpenAI": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "Groq (Llama-3)": os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        "Together (Mixtral/Llama)": os.getenv("TOGETHER_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"),
        "Hugging Face Inference API": os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3"),
        "Ollama (local)": os.getenv("OLLAMA_MODEL", "llama3"),
    }
    model_name = st.text_input("Model", value=default_models[provider])

    openai_key = st.text_input("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""), type="password") if provider=="OpenAI" else ""
    groq_key = st.text_input("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""), type="password") if provider.startswith("Groq") else ""
    together_key = st.text_input("TOGETHER_API_KEY", os.getenv("TOGETHER_API_KEY", ""), type="password") if provider.startswith("Together") else ""
    hf_key = st.text_input("HUGGINGFACE_API_KEY", os.getenv("HUGGINGFACE_API_KEY", ""), type="password") if provider.startswith("Hugging Face") else ""

    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
    

# ---------------- Input Section ----------------
st.markdown('<div class="card">', unsafe_allow_html=True)
tab_text, tab_pdf = st.tabs(["✍️ Paste Text", "📎 Upload PDF"])

user_text = ""
with tab_text:
    user_text = st.text_area(
        "Paste your letter or message here",
        height=220,
        placeholder="Fügen Sie hier den Brief ein... / Paste the letter content here..."
    )

with tab_pdf:
    pdf_file = st.file_uploader("Upload a PDF letter (optional)", type=["pdf"])
    if pdf_file is not None:
        try:
            reader = PdfReader(pdf_file)
            pdf_text = [page.extract_text() or "" for page in reader.pages]
            extracted_text = "\n".join(pdf_text).strip()
            if extracted_text:
                st.success("Extracted text from PDF. Switch to 'Paste Text' tab to edit if you like.")
                if not user_text:
                    user_text = extracted_text
            else:
                st.warning("Could not extract text from this PDF.")
        except Exception as e:
            st.error(f"PDF processing error: {e}")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
col1, col2 = st.columns([2, 1])
with col1:
    task = st.selectbox("Choose AI action", [
        "Summarize (Plain Language)",
        "Extract Key Details",
        "Draft a Reply (German)",
        "Translate to English",
        "Translate to Plain German",
        "Create Action Checklist",
    ])
with col2:
    tone = st.selectbox("Tone (for drafting)", [
        "Neutral/Professional", "Polite & Warm", "Formal", "Direct & Concise"
    ], index=0)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
extra_context = st.text_area("Optional context for better results", height=100, placeholder="e.g., I'm a student, need an extension until DD.MM.YYYY...")
st.markdown('</div>', unsafe_allow_html=True)

# --------------- Prompt builder ---------------
SYSTEM = "You are an expert assistant for German administrative letters. Be precise, structured, and helpful."

def build_user_prompt(task, text, tone, extra):
    prompts = {
        "Summarize (Plain Language)": f"Summarize this letter in very plain language (max 8 bullets). Include who, what, deadlines, actions, costs.\n\nTEXT:\n{text}\n\nEXTRA:\n{extra}",
        "Extract Key Details": f"Extract structured key details as bullet points: Sender, Subject, Reference numbers, Dates, Required actions & documents, Contact info. Keep language consistent with input.\n\nTEXT:\n{text}\n\nEXTRA:\n{extra}",
        "Draft a Reply (German)": f"Draft a polite German reply email/letter. Tone: {tone}. Keep 8–12 sentences, include placeholders if data is missing, ask clarifying questions, close with polite sign-off.\n\nINPUT LETTER:\n{text}\n\nEXTRA:\n{extra}",
        "Translate to English": f"Translate the following text to clear English. Add short clarifications for administrative terms if useful.\n\nTEXT:\n{text}",
        "Translate to Plain German": f"Rewrite the following in leichte, einfache Sprache (A2–B1). Keep facts, simplify sentences.\n\nTEXT:\n{text}",
        "Create Action Checklist": f"Create a concise checklist with deadlines and documents needed. Use checkbox-like bullets.\n\nTEXT:\n{text}",
    }
    return prompts.get(task, text)

# --------------- Provider call ---------------
def call_chat_provider(provider: str, model: str, messages: List[Dict], temperature: float = 0.2) -> str:
    if provider == "OpenAI":
        from openai import OpenAI
        api_key = openai_key or os.getenv("OPENAI_API_KEY", "")
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
        return resp.choices[0].message.content

    if provider.startswith("Groq"):
        from groq import Groq
        client = Groq(api_key=groq_key)
        resp = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
        return resp.choices[0].message.content

    if provider.startswith("Together"):
        from together import Together
        client = Together(api_key=together_key)
        resp = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
        return resp.choices[0].message.content

    if provider.startswith("Hugging Face"):
        from huggingface_hub import InferenceClient
        client = InferenceClient(model=model, token=hf_key)
        sys_txt = "\n".join(m["content"] for m in messages if m["role"] == "system")
        usr_txt = "\n".join(m["content"] for m in messages if m["role"] == "user")
        return client.text_generation(prompt=(sys_txt + "\n\n" + usr_txt), max_new_tokens=800, temperature=temperature, do_sample=True)

    if provider.startswith("Ollama"):
        url = "http://localhost:11434/api/chat"
        payload = {"model": model, "messages": messages, "stream": False, "options": {"temperature": temperature}}
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")

    return ""

# --------------- Run ---------------
run = st.button("✨ Run AI", type="primary", use_container_width=False)
output_text = st.session_state.get("output_text", "")

if run:
    if not (user_text and user_text.strip()):
        st.error("Please paste text or upload a PDF first.")
    else:
        with st.spinner("Thinking..."):
            user_prompt = build_user_prompt(task, user_text.strip(), tone, extra_context.strip())
            output_text = call_chat_provider(
                provider=provider,
                model=model_name,
                messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_prompt}],
                temperature=temperature,
            )
            st.session_state["output_text"] = output_text

# --------------- Editable result ---------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("📝 Editable Result")
edited = st.text_area("You can freely edit the AI result before saving:", value=output_text, height=300, placeholder="Your result will appear here...")
st.session_state["output_text"] = edited
st.markdown('</div>', unsafe_allow_html=True)

# --------------- Downloads (Word / PDF) ---------------
docx_buffer = BytesIO()
doc = Document()
doc.add_paragraph(edited or "")
doc.save(docx_buffer)
docx_buffer.seek(0)

pdf_buffer = BytesIO()
c = canvas.Canvas(pdf_buffer, pagesize=A4)
text_obj = c.beginText(50, 800)
for line in (edited or "").split("\n"):
    text_obj.textLine(line)
c.drawText(text_obj); c.showPage(); c.save()
pdf_buffer.seek(0)

c1, c2 = st.columns(2)
with c1:
    st.download_button(
        "💾 Download as Word (.docx)",
        data=docx_buffer,
        file_name="bureaucracy_buddy_result.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )
with c2:
    st.download_button(
        "💾 Download as PDF",
        data=pdf_buffer,
        file_name="bureaucracy_buddy_result.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

st.markdown("---")
st.caption("Tip: If you launched from Spyder, the app runs via Streamlit in your browser.")
